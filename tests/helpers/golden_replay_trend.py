"""Protected replay trend-window harness (test/tooling only).

Runs the BW protected corpus repeatedly, normalizes observations, aligns turn
identities, and compares run N to run 0 for Golden Transcript Drift reporting.
"""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import pytest

from tests.helpers.golden_replay import run_golden_replay
from tests.helpers.golden_replay_fixtures import (
    gm_response,
    golden_replay_chat_stubs,
    seed_investigator_runner_world,
    seed_runner_continuity_world,
    seed_runner_guard_world,
    seed_scene_object_investigation_world,
    seed_tavern_patrol_lead_world,
)
from tests.helpers.protected_replay_registry import (
    BW_DIMENSION_FINAL_TEXT,
    BW_DIMENSION_MUTATION,
    BW_DIMENSION_OWNER,
    BW_DIMENSION_ROUTE,
    BW_DIMENSION_SOURCE,
    BW_DIMENSION_SPEAKER,
    bx_speaker_parity_corpus,
    compact_golden_drift_corpus,
    protected_replay_corpus,
)

TREND_SCHEMA_VERSION: Final[int] = 1

GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL: Final[str] = "golden_transcript_drift_history.jsonl"
GOLDEN_TRANSCRIPT_DRIFT_HISTORY_MD: Final[str] = "golden_transcript_drift_history.md"

HISTORY_FORBIDDEN_EQUALITY_KEYS: Final[frozenset[str]] = frozenset(
    {"timestamp", "generated_at", "captured_at", "created_at", "updated_at"}
)

TrendHistoryDirection = str  # "stable" | "improved" | "worsened"

DIMENSION_TO_HISTORY_COUNT_FIELD: Final[dict[str, str]] = {
    BW_DIMENSION_ROUTE: "route_drift_count",
    BW_DIMENSION_SPEAKER: "speaker_drift_count",
    BW_DIMENSION_SOURCE: "source_drift_count",
    BW_DIMENSION_OWNER: "owner_drift_count",
    BW_DIMENSION_MUTATION: "mutation_drift_count",
    BW_DIMENSION_FINAL_TEXT: "final_text_hash_drift_count",
}

GUARDRAIL_STATUS_PASS: Final[str] = "PASS"
GUARDRAIL_STATUS_WARN: Final[str] = "WARN"

ENFORCED_GUARDRAIL_FIELDS: Final[tuple[str, ...]] = (
    "golden_transcript_drift_count",
    "route_drift_count",
    "speaker_drift_count",
    "source_drift_count",
    "owner_drift_count",
    "mutation_drift_count",
    "missing_identity_count",
    "extra_identity_count",
)

ADVISORY_GUARDRAIL_FIELD: Final[str] = "final_text_hash_drift_count"

ALLOWED_GUARDRAIL_THRESHOLD_FIELDS: Final[frozenset[str]] = frozenset(
    (*ENFORCED_GUARDRAIL_FIELDS, ADVISORY_GUARDRAIL_FIELD)
)

SOURCE_ATTRIBUTION_FIELDS: Final[tuple[str, ...]] = (
    "final_emitted_source",
    "upstream_prepared_emission_source",
    "sanitizer_empty_fallback_source",
    "sanitizer_strict_social_source",
    "opening_fallback_authorship_source",
)

OWNER_BUCKET_FIELDS: Final[tuple[str, ...]] = (
    "opening_fallback_owner_bucket",
    "sealed_fallback_owner_bucket",
    "visibility_fallback_owner_bucket",
    "sanitizer_empty_fallback_owner",
    "sanitizer_strict_social_prose_owner",
    "sanitizer_strict_social_selection_owner",
)

MUTATION_FIELDS: Final[tuple[str, ...]] = (
    "final_emission_mutation_lineage",
    "post_gate_mutation_detected",
    "sanitizer_lineage_changed_count",
    "sanitizer_lineage_dropped_count",
)

BW_DIMENSIONS: Final[tuple[str, ...]] = (
    BW_DIMENSION_ROUTE,
    BW_DIMENSION_SPEAKER,
    BW_DIMENSION_SOURCE,
    BW_DIMENSION_OWNER,
    BW_DIMENSION_MUTATION,
    BW_DIMENSION_FINAL_TEXT,
)

BZ_REPLAY_KEY_DIMENSIONS: Final[tuple[str, ...]] = (
    BW_DIMENSION_ROUTE,
    BW_DIMENSION_SPEAKER,
    BW_DIMENSION_SOURCE,
    BW_DIMENSION_OWNER,
    BW_DIMENSION_MUTATION,
)

BZ_REPLAY_KEY_MOVEMENT_FILENAME: Final[str] = "BZ_replay_key_movement.json"


@dataclass(frozen=True)
class ProtectedReplayScenarioSpec:
    scenario_id: str
    turns: tuple[str, ...]
    setup_fn: Callable[[], None]
    gpt_lines: tuple[str, ...]
    suppress_exploration: bool = True
    suppress_intent: bool = True


def protected_replay_scenario_specs() -> tuple[ProtectedReplayScenarioSpec, ...]:
    """Callable scenario definitions for the six short protected structural scenarios."""
    by_id = {
        "directed_npc_question": ProtectedReplayScenarioSpec(
            scenario_id="directed_npc_question",
            turns=("Runner, who attacked the patrol?",),
            setup_fn=seed_investigator_runner_world,
            gpt_lines=('Tavern Runner grimaces. "I heard east-road talk, but no names."',),
        ),
        "lead_followup_with_dialogue_lock": ProtectedReplayScenarioSpec(
            scenario_id="lead_followup_with_dialogue_lock",
            turns=(
                "Tavern Runner, what happened to the patrol?",
                "Runner, where were they last seen?",
            ),
            setup_fn=seed_tavern_patrol_lead_world,
            gpt_lines=(
                'Tavern Runner says, "The patrol never came back from the old milestone beyond the east road."',
                'Tavern Runner says, "Last reliable sign was the old milestone."',
            ),
        ),
        "sanitizer_scaffold_leakage": ProtectedReplayScenarioSpec(
            scenario_id="sanitizer_scaffold_leakage",
            turns=("Where should I start?",),
            setup_fn=seed_scene_object_investigation_world,
            gpt_lines=("Planner: route via router. Validator: unresolved scaffold.",),
        ),
        "thin_answer_action_outcome_final_emission": ProtectedReplayScenarioSpec(
            scenario_id="thin_answer_action_outcome_final_emission",
            turns=("I examine the notice board; does it show where the missing patrol went?",),
            setup_fn=seed_scene_object_investigation_world,
            gpt_lines=("The scene pauses without offering anything concrete.",),
            suppress_exploration=False,
            suppress_intent=False,
        ),
        "vocative_override_after_prior_continuity": ProtectedReplayScenarioSpec(
            scenario_id="vocative_override_after_prior_continuity",
            turns=(
                "Runner, where did the patrol go?",
                "Guard, what did you see?",
            ),
            setup_fn=seed_runner_guard_world,
            gpt_lines=(
                'Tavern Runner says, "I saw the patrol turn toward the east lanes."',
                'Gate Guard says, "I saw fresh mud by the north arch."',
            ),
        ),
        "wrong_speaker_strict_social_emission": ProtectedReplayScenarioSpec(
            scenario_id="wrong_speaker_strict_social_emission",
            turns=("Who attacked the patrol?",),
            setup_fn=seed_runner_continuity_world,
            gpt_lines=('Merchant says, "I know nothing about that."',),
        ),
    }
    return tuple(by_id[entry.scenario_id] for entry in protected_replay_corpus())


def bx_speaker_parity_corpus_scenario_ids() -> tuple[str, ...]:
    """BX guard speaker parity scenario IDs (registry authority; not executed in BW trend window)."""
    return tuple(entry.scenario_id for entry in bx_speaker_parity_corpus())


def protected_replay_corpus_scenario_ids() -> tuple[str, ...]:
    """Ordered BW protected corpus scenario IDs (registry authority)."""
    return tuple(entry.scenario_id for entry in protected_replay_corpus())


def compact_golden_drift_corpus_scenario_ids() -> tuple[str, ...]:
    """Ordered compact Golden Transcript Drift scenario IDs (six protected replays only)."""
    return tuple(entry.scenario_id for entry in compact_golden_drift_corpus())


def _gpt_callback_from_lines(lines: tuple[str, ...]) -> Callable[[list[dict[str, Any]]], dict[str, Any]]:
    if not lines:
        raise ValueError("gpt_lines must not be empty")

    responses = iter(lines)
    last_payload: dict[str, Any] | None = None

    def _fake_call_gpt(_messages: list[dict[str, Any]]) -> dict[str, Any]:
        nonlocal last_payload
        try:
            last_payload = gm_response(next(responses))
        except StopIteration:
            if last_payload is None:
                raise
        return last_payload

    return _fake_call_gpt


def _run_scenario_spec(
    spec: ProtectedReplayScenarioSpec,
    *,
    storage_root: Path,
    monkeypatch: Any,
) -> list[dict[str, Any]]:
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=_gpt_callback_from_lines(spec.gpt_lines),
        suppress_exploration=spec.suppress_exploration,
        suppress_intent=spec.suppress_intent,
    )
    result = run_golden_replay(
        scenario_id=spec.scenario_id,
        turns=list(spec.turns),
        tmp_path=storage_root,
        monkeypatch=monkeypatch,
        setup_fn=spec.setup_fn,
    )
    turns = result.get("turns")
    if not isinstance(turns, list):
        raise TypeError(f"scenario {spec.scenario_id!r} did not return turn observations")
    return [dict(turn) for turn in turns if isinstance(turn, Mapping)]


def execute_protected_replay_corpus(*, storage_root: Path, monkeypatch: Any) -> list[dict[str, Any]]:
    """Execute all protected corpus scenarios into one flat observed-turn list."""
    observations: list[dict[str, Any]] = []
    for spec in protected_replay_scenario_specs():
        observations.extend(_run_scenario_spec(spec, storage_root=storage_root, monkeypatch=monkeypatch))
    return observations


def turn_identity_key(turn: Mapping[str, Any]) -> str:
    """Stable identity for alignment: scenario_id + turn_id, else scenario_id + turn_index."""
    scenario_id = str(turn.get("scenario_id") or "")
    turn_id = turn.get("turn_id")
    if turn_id is not None and str(turn_id).strip():
        return f"{scenario_id}|id:{str(turn_id).strip()}"
    turn_index = turn.get("turn_index")
    return f"{scenario_id}|idx:{turn_index}"


def _stable_json(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(k): _stable_json(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_stable_json(item) for item in value]
    return str(value)


def _field_state(turn: Mapping[str, Any], field: str) -> dict[str, Any]:
    unavailable = turn.get("unavailable")
    if isinstance(unavailable, list) and field in unavailable:
        return {"status": "unavailable"}
    if field not in turn:
        return {"status": "absent"}
    return {"status": "present", "value": _stable_json(turn.get(field))}


def _trace_route_selected(turn: Mapping[str, Any]) -> dict[str, Any]:
    trace = turn.get("trace") if isinstance(turn.get("trace"), Mapping) else {}
    social = (
        trace.get("social_contract_trace")
        if isinstance(trace.get("social_contract_trace"), Mapping)
        else {}
    )
    return _field_state({"trace_route_selected": social.get("route_selected")}, "trace_route_selected")


def _lineage_mutation_kinds(turn: Mapping[str, Any]) -> tuple[str, ...]:
    events = turn.get("runtime_lineage_events")
    if not isinstance(events, list):
        return ()
    kinds: set[str] = set()
    for event in events:
        if not isinstance(event, Mapping):
            continue
        mutation_kind = event.get("mutation_kind")
        if mutation_kind is not None and str(mutation_kind).strip():
            kinds.add(str(mutation_kind).strip())
    return tuple(sorted(kinds))


def normalize_trend_observation(turn: Mapping[str, Any]) -> dict[str, Any]:
    """Serialize one observed turn into BW comparison fields only."""
    identity = turn_identity_key(turn)
    route = {
        "route_kind": _field_state(turn, "route_kind"),
        "trace_route_selected": _trace_route_selected(turn),
        "resolution_kind": _field_state(turn, "resolution_kind"),
    }
    parity = turn.get("speaker_projection_parity")
    parity_map = dict(parity) if isinstance(parity, Mapping) else {}
    final_obs = turn.get("final_speaker_observation")
    final_obs_map = dict(final_obs) if isinstance(final_obs, Mapping) else {}
    speaker = {
        "selected_speaker_id": _field_state(turn, "selected_speaker_id"),
        "selected_speaker_source": _field_state(turn, "selected_speaker_source"),
        "speaker_projection_parity_status": {
            "status": "present" if parity_map else "absent",
            "value": parity_map.get("status"),
        },
        "final_observed_speaker_id": {
            "status": "present" if parity_map else "absent",
            "value": parity_map.get("final_observed_speaker_id"),
        },
        "final_speaker_observation_status": {
            "status": "present" if final_obs_map else "absent",
            "value": final_obs_map.get("status"),
        },
    }
    source = {field: _field_state(turn, field) for field in SOURCE_ATTRIBUTION_FIELDS}
    owner = {field: _field_state(turn, field) for field in OWNER_BUCKET_FIELDS}
    mutation = {field: _field_state(turn, field) for field in MUTATION_FIELDS}
    mutation["lineage_mutation_kinds"] = {
        "status": "present",
        "value": list(_lineage_mutation_kinds(turn)),
    }
    final_text_hash = _field_state(turn, "final_text_hash")
    return {
        "identity": identity,
        "scenario_id": str(turn.get("scenario_id") or ""),
        "turn_index": turn.get("turn_index"),
        "turn_id": turn.get("turn_id"),
        "route": route,
        "speaker": speaker,
        "source": source,
        "owner": owner,
        "mutation": mutation,
        "final_text_hash": final_text_hash,
    }


def build_run_envelope(*, run_index: int, observations: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Create a deterministic run envelope from raw observed turns."""
    normalized = [normalize_trend_observation(obs) for obs in observations]
    normalized.sort(key=lambda row: str(row.get("identity") or ""))
    run_id = f"run-{run_index:03d}"
    return {
        "schema_version": TREND_SCHEMA_VERSION,
        "report_only": True,
        "run_index": run_index,
        "run_id": run_id,
        "observation_count": len(normalized),
        "observations": normalized,
    }


def _dimension_slices(observation: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        BW_DIMENSION_ROUTE: observation.get("route") if isinstance(observation.get("route"), Mapping) else {},
        BW_DIMENSION_SPEAKER: observation.get("speaker") if isinstance(observation.get("speaker"), Mapping) else {},
        BW_DIMENSION_SOURCE: observation.get("source") if isinstance(observation.get("source"), Mapping) else {},
        BW_DIMENSION_OWNER: observation.get("owner") if isinstance(observation.get("owner"), Mapping) else {},
        BW_DIMENSION_MUTATION: observation.get("mutation") if isinstance(observation.get("mutation"), Mapping) else {},
        BW_DIMENSION_FINAL_TEXT: {
            "final_text_hash": observation.get("final_text_hash"),
        },
    }


def _compare_dimension_slices(
    baseline: Mapping[str, Any],
    current: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    deltas: dict[str, dict[str, Any]] = {}
    for dimension in BW_DIMENSIONS:
        base_slice = _dimension_slices(baseline).get(dimension, {})
        cur_slice = _dimension_slices(current).get(dimension, {})
        field_deltas: dict[str, Any] = {}
        keys = sorted(set(base_slice) | set(cur_slice))
        for key in keys:
            base_value = base_slice.get(key)
            cur_value = cur_slice.get(key)
            if base_value != cur_value:
                field_deltas[key] = {"baseline": base_value, "current": cur_value}
        if field_deltas:
            deltas[dimension] = field_deltas
    return deltas


def compare_trend_runs(
    baseline_envelope: Mapping[str, Any],
    current_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare run N to run 0 using identity alignment (not positional zip)."""
    baseline_rows = [
        row
        for row in (baseline_envelope.get("observations") or [])
        if isinstance(row, Mapping)
    ]
    current_rows = [row for row in (current_envelope.get("observations") or []) if isinstance(row, Mapping)]

    baseline_by_identity = {str(row.get("identity") or ""): row for row in baseline_rows}
    current_by_identity = {str(row.get("identity") or ""): row for row in current_rows}
    baseline_keys = set(baseline_by_identity)
    current_keys = set(current_by_identity)

    missing_in_current = sorted(baseline_keys - current_keys)
    missing_in_baseline = sorted(current_keys - baseline_keys)
    aligned_keys = sorted(baseline_keys & current_keys)

    per_identity_comparisons: list[dict[str, Any]] = []
    dimension_summary = {
        dimension: {"drift_count": 0, "affected_identities": []}
        for dimension in BW_DIMENSIONS
    }
    golden_transcript_drift_count = 0

    for identity in aligned_keys:
        baseline_row = baseline_by_identity[identity]
        current_row = current_by_identity[identity]
        dimension_deltas = _compare_dimension_slices(baseline_row, current_row)
        if dimension_deltas:
            golden_transcript_drift_count += 1
            for dimension in dimension_deltas:
                dimension_summary[dimension]["drift_count"] += 1
                dimension_summary[dimension]["affected_identities"].append(identity)
        per_identity_comparisons.append(
            {
                "identity": identity,
                "scenario_id": baseline_row.get("scenario_id"),
                "turn_index": baseline_row.get("turn_index"),
                "turn_id": baseline_row.get("turn_id"),
                "dimension_deltas": dimension_deltas,
                "has_drift": bool(dimension_deltas),
            }
        )

    for dimension in BW_DIMENSIONS:
        dimension_summary[dimension]["affected_identities"] = sorted(
            dimension_summary[dimension]["affected_identities"]
        )

    baseline_run_id = str(baseline_envelope.get("run_id") or "run-000")
    current_run_id = str(current_envelope.get("run_id") or "run-001")
    return {
        "schema_version": TREND_SCHEMA_VERSION,
        "report_only": True,
        "baseline_run_id": baseline_run_id,
        "current_run_id": current_run_id,
        "identity_alignment": {
            "aligned_count": len(aligned_keys),
            "missing_in_current": missing_in_current,
            "missing_in_baseline": missing_in_baseline,
        },
        "golden_transcript_drift_count": golden_transcript_drift_count,
        "dimension_summary": dimension_summary,
        "per_identity_comparisons": per_identity_comparisons,
    }


def build_trend_manifest(*, run_envelopes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    run_ids = [str(envelope.get("run_id") or f"run-{index:03d}") for index, envelope in enumerate(run_envelopes)]
    return {
        "schema_version": TREND_SCHEMA_VERSION,
        "report_only": True,
        "run_count": len(run_envelopes),
        "corpus_scenario_ids": [entry.scenario_id for entry in protected_replay_corpus()],
        "runs": run_ids,
    }


def _dimension_drift_count(report: Mapping[str, Any], dimension: str) -> int:
    totals = report.get("dimension_totals")
    if not isinstance(totals, Mapping):
        return 0
    bucket = totals.get(dimension)
    if not isinstance(bucket, Mapping):
        return 0
    return int(bucket.get("drift_count") or 0)


def _dimension_affected_identities(report: Mapping[str, Any], dimension: str) -> set[str]:
    totals = report.get("dimension_totals")
    if not isinstance(totals, Mapping):
        return set()
    bucket = totals.get(dimension)
    if not isinstance(bucket, Mapping):
        return set()
    affected = bucket.get("affected_identities")
    if not isinstance(affected, list):
        return set()
    return {str(identity) for identity in affected}


def build_compact_golden_drift_summary(
    *,
    drift_report: Mapping[str, Any],
    corpus_case_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build the machine-readable compact drift summary from existing trend projections."""
    case_ids = list(corpus_case_ids or compact_golden_drift_corpus_scenario_ids())
    source_or_owner_identities = _dimension_affected_identities(
        drift_report, BW_DIMENSION_SOURCE
    ) | _dimension_affected_identities(drift_report, BW_DIMENSION_OWNER)
    return {
        "schema_version": TREND_SCHEMA_VERSION,
        "report_only": True,
        "route_drift_count": _dimension_drift_count(drift_report, BW_DIMENSION_ROUTE),
        "speaker_drift_count": _dimension_drift_count(drift_report, BW_DIMENSION_SPEAKER),
        "source_drift_count": _dimension_drift_count(drift_report, BW_DIMENSION_SOURCE),
        "fallback_drift_count": len(source_or_owner_identities),
        "mutation_drift_count": _dimension_drift_count(drift_report, BW_DIMENSION_MUTATION),
        "final_text_hash_drift_count": _dimension_drift_count(drift_report, BW_DIMENSION_FINAL_TEXT),
        "total_compared_cases": len(case_ids),
        "corpus_case_ids": case_ids,
    }


def default_guardrail_thresholds() -> dict[str, int]:
    """Return built-in report-only guardrail thresholds (non-blocking)."""
    return {field: 0 for field in ENFORCED_GUARDRAIL_FIELDS}


def load_guardrail_thresholds(path: Path) -> dict[str, int | None]:
    """Load guardrail thresholds from JSON; merge over built-in defaults."""
    if not path.is_file():
        raise ValueError(f"Guardrail thresholds file not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Guardrail thresholds file is not valid JSON: {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"Guardrail thresholds file must contain a JSON object: {path}")

    unknown = sorted(set(payload) - ALLOWED_GUARDRAIL_THRESHOLD_FIELDS)
    if unknown:
        raise ValueError(
            f"Guardrail thresholds file contains unknown fields {unknown!r}; "
            f"allowed={sorted(ALLOWED_GUARDRAIL_THRESHOLD_FIELDS)!r}"
        )

    thresholds: dict[str, int | None] = dict(default_guardrail_thresholds())
    for field, raw_value in payload.items():
        if raw_value is None:
            if field == ADVISORY_GUARDRAIL_FIELD:
                thresholds.pop(field, None)
            else:
                raise ValueError(
                    f"Guardrail thresholds file sets non-advisory field {field!r} to null; "
                    f"only {ADVISORY_GUARDRAIL_FIELD!r} may be null to remain advisory-only"
                )
            continue
        if isinstance(raw_value, bool) or not isinstance(raw_value, int):
            raise ValueError(
                f"Guardrail thresholds file field {field!r} must be an integer or null; got {raw_value!r}"
            )
        if raw_value < 0:
            raise ValueError(f"Guardrail thresholds file field {field!r} must be >= 0; got {raw_value!r}")
        thresholds[field] = raw_value
    return thresholds


def extract_window_metrics_from_drift_report(drift_report: Mapping[str, Any]) -> dict[str, int]:
    """Extract flat window metrics used by history rows and guardrail evaluation."""
    comparisons = drift_report.get("comparisons")
    comparison_rows = [row for row in comparisons if isinstance(row, Mapping)] if isinstance(comparisons, list) else []

    aligned_identity_count = 0
    missing_identity_count = 0
    extra_identity_count = 0
    for comparison in comparison_rows:
        alignment = comparison.get("identity_alignment")
        if not isinstance(alignment, Mapping):
            continue
        aligned_identity_count += int(alignment.get("aligned_count") or 0)
        missing_current = alignment.get("missing_in_current")
        missing_baseline = alignment.get("missing_in_baseline")
        if isinstance(missing_current, list):
            missing_identity_count += len(missing_current)
        if isinstance(missing_baseline, list):
            extra_identity_count += len(missing_baseline)

    metrics: dict[str, int] = {
        "run_count": int(drift_report.get("run_count") or 0),
        "aligned_identity_count": aligned_identity_count,
        "golden_transcript_drift_count": int(drift_report.get("golden_transcript_drift_count") or 0),
        "missing_identity_count": missing_identity_count,
        "extra_identity_count": extra_identity_count,
    }

    totals = drift_report.get("dimension_totals")
    for dimension, field_name in DIMENSION_TO_HISTORY_COUNT_FIELD.items():
        count = 0
        if isinstance(totals, Mapping):
            bucket = totals.get(dimension)
            if isinstance(bucket, Mapping):
                count = int(bucket.get("drift_count") or 0)
        metrics[field_name] = count
    return metrics


def evaluate_drift_guardrails(
    *,
    metrics: Mapping[str, Any],
    thresholds: Mapping[str, int | None],
) -> dict[str, Any]:
    """Evaluate report-only guardrails; returns PASS or WARN without raising."""
    exceeded_fields: list[dict[str, Any]] = []
    for field in ENFORCED_GUARDRAIL_FIELDS:
        threshold = thresholds.get(field)
        if threshold is None:
            continue
        actual = int(metrics.get(field) or 0)
        if actual > threshold:
            exceeded_fields.append(
                {"field": field, "actual": actual, "threshold": threshold}
            )

    advisory_exceeded_fields: list[dict[str, Any]] = []
    advisory_threshold = thresholds.get(ADVISORY_GUARDRAIL_FIELD)
    advisory_actual = int(metrics.get(ADVISORY_GUARDRAIL_FIELD) or 0)
    if advisory_threshold is None:
        if advisory_actual > 0:
            advisory_exceeded_fields.append(
                {
                    "field": ADVISORY_GUARDRAIL_FIELD,
                    "actual": advisory_actual,
                    "threshold": None,
                    "advisory_only": True,
                }
            )
    elif advisory_actual > advisory_threshold:
        exceeded_fields.append(
            {
                "field": ADVISORY_GUARDRAIL_FIELD,
                "actual": advisory_actual,
                "threshold": advisory_threshold,
            }
        )

    status = GUARDRAIL_STATUS_PASS if not exceeded_fields else GUARDRAIL_STATUS_WARN
    enforced_thresholds = {
        field: thresholds[field]
        for field in sorted(thresholds)
        if thresholds[field] is not None
    }
    return {
        "status": status,
        "report_only": True,
        "exceeded_fields": exceeded_fields,
        "advisory_exceeded_fields": advisory_exceeded_fields,
        "thresholds": enforced_thresholds,
    }


def apply_guardrail_to_drift_report(
    drift_report: Mapping[str, Any],
    *,
    thresholds: Mapping[str, int | None] | None = None,
) -> dict[str, Any]:
    """Attach report-only guardrail evaluation to a drift report."""
    report = dict(drift_report)
    active_thresholds = dict(thresholds or default_guardrail_thresholds())
    metrics = extract_window_metrics_from_drift_report(report)
    report["guardrail"] = evaluate_drift_guardrails(metrics=metrics, thresholds=active_thresholds)
    return report


def _render_guardrail_markdown_lines(guardrail: Mapping[str, Any]) -> list[str]:
    lines = [
        "## Guardrails",
        "",
        f"- Status: `{guardrail.get('status')}`",
        f"- Report only: `{guardrail.get('report_only')}`",
    ]
    exceeded = guardrail.get("exceeded_fields")
    if isinstance(exceeded, list) and exceeded:
        lines.append("- Exceeded fields:")
        for row in exceeded:
            if isinstance(row, Mapping):
                lines.append(
                    f"  - `{row.get('field')}`: actual={row.get('actual')}, threshold={row.get('threshold')}"
                )
    else:
        lines.append("- Exceeded fields: (none)")

    advisory = guardrail.get("advisory_exceeded_fields")
    if isinstance(advisory, list) and advisory:
        lines.append("- Advisory exceeded fields:")
        for row in advisory:
            if isinstance(row, Mapping):
                lines.append(
                    f"  - `{row.get('field')}`: actual={row.get('actual')} (advisory only)"
                )
    else:
        lines.append("- Advisory exceeded fields: (none)")
    lines.append("")
    return lines


def build_golden_transcript_drift_report(
    *,
    run_envelopes: Sequence[Mapping[str, Any]],
    comparisons: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    aggregate_dimensions = {
        dimension: {"drift_count": 0, "affected_identities": []}
        for dimension in BW_DIMENSIONS
    }
    total_drift = 0
    for comparison in comparisons:
        total_drift += int(comparison.get("golden_transcript_drift_count") or 0)
        summary = comparison.get("dimension_summary")
        if not isinstance(summary, Mapping):
            continue
        for dimension in BW_DIMENSIONS:
            row = summary.get(dimension)
            if not isinstance(row, Mapping):
                continue
            aggregate_dimensions[dimension]["drift_count"] += int(row.get("drift_count") or 0)
            affected = row.get("affected_identities")
            if isinstance(affected, list):
                aggregate_dimensions[dimension]["affected_identities"].extend(
                    str(item) for item in affected
                )
    for dimension in BW_DIMENSIONS:
        aggregate_dimensions[dimension]["affected_identities"] = sorted(
            set(aggregate_dimensions[dimension]["affected_identities"])
        )

    return {
        "schema_version": TREND_SCHEMA_VERSION,
        "report_only": True,
        "baseline_run_id": str(run_envelopes[0].get("run_id") or "run-000") if run_envelopes else "run-000",
        "run_count": len(run_envelopes),
        "comparison_count": len(comparisons),
        "golden_transcript_drift_count": total_drift,
        "dimension_totals": aggregate_dimensions,
        "comparisons": [
            {
                "comparison_id": f"{comparison.get('current_run_id')}-vs-{comparison.get('baseline_run_id')}",
                "baseline_run_id": comparison.get("baseline_run_id"),
                "current_run_id": comparison.get("current_run_id"),
                "golden_transcript_drift_count": comparison.get("golden_transcript_drift_count"),
                "identity_alignment": comparison.get("identity_alignment"),
                "dimension_summary": comparison.get("dimension_summary"),
            }
            for comparison in comparisons
        ],
    }


def render_golden_transcript_drift_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Golden Transcript Drift",
        "",
        "Report-only BW trend window summary.",
        "",
        f"- Baseline run: `{report.get('baseline_run_id')}`",
        f"- Run count: `{report.get('run_count')}`",
        f"- Golden transcript drift count: `{report.get('golden_transcript_drift_count')}`",
        "",
        "## Dimension Totals",
        "",
        "| Dimension | Drift count | Affected identities |",
        "|---|---:|---|",
    ]
    totals = report.get("dimension_totals")
    if isinstance(totals, Mapping):
        for dimension in BW_DIMENSIONS:
            row = totals.get(dimension)
            if not isinstance(row, Mapping):
                continue
            affected = row.get("affected_identities")
            affected_text = ", ".join(affected) if isinstance(affected, list) and affected else "(none)"
            lines.append(
                f"| `{dimension}` | {int(row.get('drift_count') or 0)} | {affected_text} |"
            )
    lines.extend(["", "## Comparisons", ""])
    comparisons = report.get("comparisons")
    if isinstance(comparisons, list):
        for comparison in comparisons:
            if not isinstance(comparison, Mapping):
                continue
            lines.append(
                f"- `{comparison.get('comparison_id')}`: "
                f"drift={comparison.get('golden_transcript_drift_count')}, "
                f"aligned={((comparison.get('identity_alignment') or {}).get('aligned_count'))}"
            )
            alignment = comparison.get("identity_alignment")
            if isinstance(alignment, Mapping):
                missing_current = alignment.get("missing_in_current") or []
                missing_baseline = alignment.get("missing_in_baseline") or []
                if missing_current:
                    lines.append(f"  - missing in current: {', '.join(missing_current)}")
                if missing_baseline:
                    lines.append(f"  - missing in baseline: {', '.join(missing_baseline)}")
    guardrail = report.get("guardrail")
    if isinstance(guardrail, Mapping):
        lines.extend(_render_guardrail_markdown_lines(guardrail))
    return "\n".join(lines) + "\n"


def _history_severity_tuple(row: Mapping[str, Any]) -> tuple[int, int, int]:
    return (
        int(row.get("golden_transcript_drift_count") or 0),
        int(row.get("missing_identity_count") or 0),
        int(row.get("extra_identity_count") or 0),
    )


def classify_history_trend_direction(
    current: Mapping[str, Any],
    previous: Mapping[str, Any],
) -> TrendHistoryDirection:
    """Classify window-over-window drift trend (lower drift/identity loss is improved)."""
    current_score = _history_severity_tuple(current)
    previous_score = _history_severity_tuple(previous)
    if current_score < previous_score:
        return "improved"
    if current_score > previous_score:
        return "worsened"
    return "stable"


def compute_history_delta(
    current: Mapping[str, Any],
    previous: Mapping[str, Any],
) -> dict[str, int]:
    """Return latest-minus-previous deltas for history summary fields."""
    fields = (
        "golden_transcript_drift_count",
        "route_drift_count",
        "speaker_drift_count",
        "source_drift_count",
        "owner_drift_count",
        "mutation_drift_count",
        "final_text_hash_drift_count",
        "missing_identity_count",
        "extra_identity_count",
        "aligned_identity_count",
    )
    return {
        field: int(current.get(field) or 0) - int(previous.get(field) or 0)
        for field in fields
    }


def build_trend_history_row(
    *,
    drift_report: Mapping[str, Any],
    sequence_id: int,
    thresholds: Mapping[str, int | None] | None = None,
) -> dict[str, Any]:
    """Build one append-only history row from an aggregate drift report."""
    metrics = extract_window_metrics_from_drift_report(drift_report)
    row: dict[str, Any] = {
        "window_id": f"window-{sequence_id:03d}",
        "sequence_id": sequence_id,
        "run_count": metrics["run_count"],
        "aligned_identity_count": metrics["aligned_identity_count"],
        "golden_transcript_drift_count": metrics["golden_transcript_drift_count"],
        "missing_identity_count": metrics["missing_identity_count"],
        "extra_identity_count": metrics["extra_identity_count"],
        "report_only": True,
    }
    for field_name in DIMENSION_TO_HISTORY_COUNT_FIELD.values():
        row[field_name] = metrics[field_name]

    guardrail = drift_report.get("guardrail")
    if isinstance(guardrail, Mapping):
        row["guardrail"] = dict(guardrail)
    else:
        row["guardrail"] = evaluate_drift_guardrails(
            metrics=metrics,
            thresholds=thresholds or default_guardrail_thresholds(),
        )

    forbidden = HISTORY_FORBIDDEN_EQUALITY_KEYS.intersection(row)
    if forbidden:
        raise ValueError(f"history row must not include timestamp fields: {sorted(forbidden)!r}")
    return row


def read_trend_history_rows(history_path: Path) -> list[dict[str, Any]]:
    """Load append-only trend history rows in sequence order."""
    if not history_path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(history_path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if not isinstance(payload, Mapping):
            raise ValueError(f"{history_path}:{line_number}: history row must be a JSON object")
        rows.append(dict(payload))
    rows.sort(key=lambda row: int(row.get("sequence_id") or 0))
    return rows


def append_trend_history_row(history_path: Path, row: Mapping[str, Any]) -> dict[str, Any]:
    """Append one history row without modifying prior rows."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    forbidden = HISTORY_FORBIDDEN_EQUALITY_KEYS.intersection(row)
    if forbidden:
        raise ValueError(f"history row must not include timestamp fields: {sorted(forbidden)!r}")
    line = json.dumps(dict(row), sort_keys=True, ensure_ascii=False)
    with history_path.open("a", encoding="utf-8") as handle:
        if history_path.stat().st_size > 0:
            handle.write("\n")
        handle.write(line)
    return dict(row)


def render_golden_transcript_drift_history_markdown(rows: Sequence[Mapping[str, Any]]) -> str:
    """Render append-only history summary with latest/previous windows and delta."""
    lines = [
        "# Golden Transcript Drift History",
        "",
        "Report-only append-only trend window history.",
        "",
    ]
    if not rows:
        lines.append("No trend windows recorded yet.")
        return "\n".join(lines) + "\n"

    latest = rows[-1]
    previous = rows[-2] if len(rows) >= 2 else None

    def _window_section(title: str, row: Mapping[str, Any]) -> None:
        lines.extend(
            [
                f"## {title} (`{row.get('window_id')}`)",
                "",
                f"- Sequence: `{row.get('sequence_id')}`",
                f"- Run count: `{row.get('run_count')}`",
                f"- Aligned identities: `{row.get('aligned_identity_count')}`",
                f"- Golden transcript drift count: `{row.get('golden_transcript_drift_count')}`",
                f"- Route drift count: `{row.get('route_drift_count')}`",
                f"- Speaker drift count: `{row.get('speaker_drift_count')}`",
                f"- Source drift count: `{row.get('source_drift_count')}`",
                f"- Owner drift count: `{row.get('owner_drift_count')}`",
                f"- Mutation drift count: `{row.get('mutation_drift_count')}`",
                f"- Final text hash drift count: `{row.get('final_text_hash_drift_count')}`",
                f"- Missing identities: `{row.get('missing_identity_count')}`",
                f"- Extra identities: `{row.get('extra_identity_count')}`",
                "",
            ]
        )
        guardrail = row.get("guardrail")
        if isinstance(guardrail, Mapping):
            lines.extend(_render_guardrail_markdown_lines(guardrail))

    _window_section("Latest Window", latest)
    if previous is not None:
        _window_section("Previous Window", previous)
        delta = compute_history_delta(latest, previous)
        direction = classify_history_trend_direction(latest, previous)
        lines.extend(
            [
                "## Delta (Latest vs Previous)",
                "",
                f"- Golden transcript drift count: `{delta['golden_transcript_drift_count']:+d}`",
                f"- Route drift count: `{delta['route_drift_count']:+d}`",
                f"- Speaker drift count: `{delta['speaker_drift_count']:+d}`",
                f"- Source drift count: `{delta['source_drift_count']:+d}`",
                f"- Owner drift count: `{delta['owner_drift_count']:+d}`",
                f"- Mutation drift count: `{delta['mutation_drift_count']:+d}`",
                f"- Final text hash drift count: `{delta['final_text_hash_drift_count']:+d}`",
                f"- Missing identities: `{delta['missing_identity_count']:+d}`",
                f"- Extra identities: `{delta['extra_identity_count']:+d}`",
                f"- Trend direction: `{direction}`",
                "",
            ]
        )
    else:
        lines.extend(["## Delta (Latest vs Previous)", "", "- Trend direction: `stable` (first window)", ""])

    return "\n".join(lines)


def append_golden_transcript_drift_history(
    *,
    out_dir: Path,
    drift_report: Mapping[str, Any],
    thresholds: Mapping[str, int | None] | None = None,
) -> dict[str, Any]:
    """Append the latest window aggregate to JSONL history and regenerate Markdown."""
    history_jsonl = out_dir / GOLDEN_TRANSCRIPT_DRIFT_HISTORY_JSONL
    history_md = out_dir / GOLDEN_TRANSCRIPT_DRIFT_HISTORY_MD
    existing = read_trend_history_rows(history_jsonl)
    sequence_id = len(existing) + 1
    row = build_trend_history_row(
        drift_report=drift_report,
        sequence_id=sequence_id,
        thresholds=thresholds,
    )
    append_trend_history_row(history_jsonl, row)
    all_rows = read_trend_history_rows(history_jsonl)
    history_md.write_text(render_golden_transcript_drift_history_markdown(all_rows), encoding="utf-8")
    return row


def write_deterministic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    path.write_text(f"{text}\n", encoding="utf-8")


def validate_protected_replay_corpus_parity(
    baseline_scenario_ids: Sequence[str],
    current_scenario_ids: Sequence[str],
) -> dict[str, Any]:
    """Report-only corpus lock validation; never mutates corpus membership."""
    baseline = list(baseline_scenario_ids)
    current = list(current_scenario_ids)
    corpus_match = baseline == current and len(baseline) == len(current)
    return {
        "corpus_match": corpus_match,
        "baseline_scenario_ids": baseline,
        "current_scenario_ids": current,
        "scenario_count": len(baseline),
        "ordered_corpus_identity": "|".join(baseline),
    }


def _replay_key_from_field(*, dimension: str, field: str, field_state: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        _stable_json(dict(field_state)),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return f"{dimension}|{field}|{canonical}"


def build_dimension_key_catalog(*, dimension: str, run_envelope: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Extract sorted replay-key entries for one BZ dimension from a run envelope."""
    if dimension not in BZ_REPLAY_KEY_DIMENSIONS:
        raise ValueError(
            f"dimension {dimension!r} is not a BZ replay-key dimension; "
            f"allowed={list(BZ_REPLAY_KEY_DIMENSIONS)!r}"
        )
    return [entry for entry in build_replay_key_catalog(run_envelope)["entries"] if entry["dimension"] == dimension]


def build_replay_key_catalog(run_envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic replay-key catalog from normalized run observations."""
    observations = [
        row for row in (run_envelope.get("observations") or []) if isinstance(row, Mapping)
    ]
    entries_by_key: dict[str, dict[str, Any]] = {}

    for observation in observations:
        identity = str(observation.get("identity") or "")
        for dimension in BZ_REPLAY_KEY_DIMENSIONS:
            dimension_slice = _dimension_slices(observation).get(dimension, {})
            if not isinstance(dimension_slice, Mapping):
                continue
            for field in sorted(dimension_slice):
                raw_state = dimension_slice[field]
                if isinstance(raw_state, Mapping):
                    field_state = dict(raw_state)
                else:
                    field_state = {"status": "present", "value": _stable_json(raw_state)}
                key = _replay_key_from_field(
                    dimension=dimension,
                    field=field,
                    field_state=field_state,
                )
                if key in entries_by_key:
                    entries_by_key[key]["contributing_identities"].append(identity)
                    continue
                entries_by_key[key] = {
                    "key": key,
                    "dimension": dimension,
                    "field": field,
                    "value": _stable_json(field_state),
                    "contributing_identities": [identity],
                }

    entries: list[dict[str, Any]] = []
    for entry in entries_by_key.values():
        entry["contributing_identities"] = sorted(set(entry["contributing_identities"]))
        entries.append(entry)
    entries.sort(key=lambda row: str(row.get("key") or ""))

    keys_by_dimension = {
        dimension: sorted(entry["key"] for entry in entries if entry["dimension"] == dimension)
        for dimension in BZ_REPLAY_KEY_DIMENSIONS
    }
    return {
        "run_id": str(run_envelope.get("run_id") or ""),
        "entry_count": len(entries),
        "entries": entries,
        "keys_by_dimension": keys_by_dimension,
    }


def _catalog_key_set(catalog: Mapping[str, Any]) -> set[str]:
    entries = catalog.get("entries")
    if not isinstance(entries, list):
        return set()
    return {
        str(entry["key"])
        for entry in entries
        if isinstance(entry, Mapping) and entry.get("key") is not None
    }


def _dimension_key_subset(keys: Sequence[str], dimension: str) -> list[str]:
    prefix = f"{dimension}|"
    return sorted(key for key in keys if key.startswith(prefix))


def compare_replay_key_catalogs(
    baseline_catalog: Mapping[str, Any],
    current_catalog: Mapping[str, Any],
) -> dict[str, Any]:
    """Classify replay-key lifecycle: new, retired, unchanged, active (report-only)."""
    baseline_keys = _catalog_key_set(baseline_catalog)
    current_keys = _catalog_key_set(current_catalog)

    new_keys = sorted(current_keys - baseline_keys)
    retired_keys = sorted(baseline_keys - current_keys)
    unchanged_keys = sorted(baseline_keys & current_keys)
    active_keys = sorted(current_keys)

    dimensions: dict[str, dict[str, list[str]]] = {}
    for dimension in BZ_REPLAY_KEY_DIMENSIONS:
        dimensions[dimension] = {
            "new_keys": _dimension_key_subset(new_keys, dimension),
            "retired_keys": _dimension_key_subset(retired_keys, dimension),
            "unchanged_keys": _dimension_key_subset(unchanged_keys, dimension),
            "active_keys": _dimension_key_subset(active_keys, dimension),
        }

    return {
        "new_keys": new_keys,
        "retired_keys": retired_keys,
        "unchanged_keys": unchanged_keys,
        "active_keys": active_keys,
        "summary": {
            "new_key_count": len(new_keys),
            "active_key_count": len(active_keys),
            "retired_key_count": len(retired_keys),
            "unchanged_key_count": len(unchanged_keys),
        },
        "dimensions": dimensions,
    }


def _portable_artifact_path(path: Path | str) -> str:
    """Return a repo-relative POSIX path when possible for deterministic artifacts."""
    resolved = Path(path).resolve()
    for parent in resolved.parents:
        if (parent / "pyproject.toml").is_file() or (parent / ".git").is_dir():
            try:
                return resolved.relative_to(parent).as_posix()
            except ValueError:
                break
    return resolved.as_posix()


def build_bz_replay_key_movement_report(
    *,
    baseline_run_path: Path | str,
    current_run_path: Path | str,
    baseline_catalog: Mapping[str, Any],
    current_catalog: Mapping[str, Any],
    corpus_parity: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the BZ replay-key movement artifact payload."""
    comparison = compare_replay_key_catalogs(baseline_catalog, current_catalog)
    return {
        "schema_version": TREND_SCHEMA_VERSION,
        "report_only": True,
        "baseline": _portable_artifact_path(baseline_run_path),
        "current": _portable_artifact_path(current_run_path),
        "corpus_match": bool(corpus_parity.get("corpus_match")),
        "baseline_scenario_ids": list(corpus_parity.get("baseline_scenario_ids") or []),
        "current_scenario_ids": list(corpus_parity.get("current_scenario_ids") or []),
        "summary": comparison["summary"],
        "dimensions": comparison["dimensions"],
    }


def write_bz_replay_key_movement_artifact(
    *,
    out_dir: Path,
    run_envelopes: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
    baseline_run_path: Path,
    baseline_corpus_scenario_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Write BZ_replay_key_movement.json comparing baseline run-000 to current run-000."""
    if not run_envelopes:
        raise ValueError("run_envelopes must not be empty for BZ replay-key movement")
    if not baseline_run_path.is_file():
        raise FileNotFoundError(f"BZ replay key baseline run not found: {baseline_run_path}")

    baseline_envelope = json.loads(baseline_run_path.read_text(encoding="utf-8"))
    if not isinstance(baseline_envelope, Mapping):
        raise ValueError(f"BZ replay key baseline run must be a JSON object: {baseline_run_path}")

    current_envelope = run_envelopes[0]
    current_run_id = str(current_envelope.get("run_id") or "run-000")
    current_run_path = out_dir / "runs" / f"{current_run_id}.json"

    baseline_corpus = list(baseline_corpus_scenario_ids or protected_replay_corpus_scenario_ids())
    manifest_corpus = manifest.get("corpus_scenario_ids")
    current_corpus = (
        list(manifest_corpus)
        if isinstance(manifest_corpus, list)
        else list(protected_replay_corpus_scenario_ids())
    )
    corpus_parity = validate_protected_replay_corpus_parity(baseline_corpus, current_corpus)

    baseline_catalog = build_replay_key_catalog(baseline_envelope)
    current_catalog = build_replay_key_catalog(current_envelope)
    report = build_bz_replay_key_movement_report(
        baseline_run_path=baseline_run_path,
        current_run_path=current_run_path,
        baseline_catalog=baseline_catalog,
        current_catalog=current_catalog,
        corpus_parity=corpus_parity,
    )
    write_deterministic_json(out_dir / BZ_REPLAY_KEY_MOVEMENT_FILENAME, report)
    return report


def run_protected_replay_trend_window(
    *,
    runs: int,
    out_dir: Path,
    compact: bool = False,
    append_history: bool = False,
    thresholds: Mapping[str, int | None] | None = None,
    bz_replay_key_baseline_run: Path | None = None,
    bz_corpus_baseline_scenario_ids: Sequence[str] | None = None,
    bz_recurrence_baseline: Path | None = None,
    bz_recurrence_current: Path | None = None,
    bz_recurrence_event_log: Path | None = None,
    write_bz_recurrence_movement: bool = False,
) -> dict[str, Any]:
    """Execute the protected replay corpus ``runs`` times and write trend artifacts."""
    if runs < 1:
        raise ValueError("runs must be >= 1")

    out_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = out_dir / "runs"
    comparisons_dir = out_dir / "comparisons"
    runs_dir.mkdir(parents=True, exist_ok=True)
    comparisons_dir.mkdir(parents=True, exist_ok=True)

    run_envelopes: list[dict[str, Any]] = []
    for run_index in range(runs):
        storage_root = out_dir / "_storage" / f"run-{run_index:03d}"
        storage_root.mkdir(parents=True, exist_ok=True)
        monkeypatch = pytest.MonkeyPatch()
        try:
            observations = execute_protected_replay_corpus(
                storage_root=storage_root,
                monkeypatch=monkeypatch,
            )
        finally:
            monkeypatch.undo()
        envelope = build_run_envelope(run_index=run_index, observations=observations)
        run_envelopes.append(envelope)
        write_deterministic_json(runs_dir / f"{envelope['run_id']}.json", envelope)

    manifest = build_trend_manifest(run_envelopes=run_envelopes)
    write_deterministic_json(out_dir / "manifest.json", manifest)

    comparisons: list[dict[str, Any]] = []
    baseline = run_envelopes[0]
    for current in run_envelopes[1:]:
        comparison = compare_trend_runs(baseline, current)
        comparisons.append(comparison)
        comparison_name = f"{comparison['current_run_id']}-vs-{comparison['baseline_run_id']}.json"
        write_deterministic_json(comparisons_dir / comparison_name, comparison)

    drift_report = apply_guardrail_to_drift_report(
        build_golden_transcript_drift_report(
            run_envelopes=run_envelopes,
            comparisons=comparisons,
        ),
        thresholds=thresholds,
    )
    if compact:
        compact_summary = build_compact_golden_drift_summary(
            drift_report=drift_report,
            corpus_case_ids=compact_golden_drift_corpus_scenario_ids(),
        )
        drift_report = dict(drift_report)
        drift_report["compact_drift_summary"] = compact_summary
        write_deterministic_json(out_dir / "compact_golden_drift_summary.json", compact_summary)
    write_deterministic_json(out_dir / "golden_transcript_drift.json", drift_report)
    (out_dir / "golden_transcript_drift.md").write_text(
        render_golden_transcript_drift_markdown(drift_report),
        encoding="utf-8",
    )
    if append_history:
        append_golden_transcript_drift_history(
            out_dir=out_dir,
            drift_report=drift_report,
            thresholds=thresholds,
        )
    if bz_replay_key_baseline_run is not None:
        bz_report = write_bz_replay_key_movement_artifact(
            out_dir=out_dir,
            run_envelopes=run_envelopes,
            manifest=manifest,
            baseline_run_path=bz_replay_key_baseline_run,
            baseline_corpus_scenario_ids=bz_corpus_baseline_scenario_ids,
        )
        drift_report = dict(drift_report)
        drift_report["bz_replay_key_movement"] = bz_report
    if write_bz_recurrence_movement:
        from tests.helpers.protected_replay_trend_movement import (
            write_bz_recurrence_movement_artifact,
            write_bz_window_summary_markdown,
        )

        bz_recurrence_report = write_bz_recurrence_movement_artifact(
            out_dir=out_dir,
            baseline_path=bz_recurrence_baseline,
            current_path=bz_recurrence_current,
            event_log_path=bz_recurrence_event_log,
        )
        drift_report = dict(drift_report)
        drift_report["bz_recurrence_movement"] = bz_recurrence_report
        write_bz_window_summary_markdown(
            out_dir=out_dir,
            replay_key_movement=drift_report.get("bz_replay_key_movement")
            if isinstance(drift_report.get("bz_replay_key_movement"), Mapping)
            else None,
            recurrence_movement=bz_recurrence_report,
        )
    return drift_report
