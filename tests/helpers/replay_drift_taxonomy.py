"""Owner-oriented replay drift bucket taxonomy (Cycle AR).

Maps existing replay measurement buckets, failure categories, and rerun deltas
into stable owner drift buckets for reporting. Read-only replay side; no runtime
imports.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

ALLOWED_OWNER_DRIFT_BUCKETS: frozenset[str] = frozenset(
    {
        "route_drift",
        "speaker_drift",
        "fallback_drift",
        "ownership_drift",
        "emission_drift",
        "semantic_drift",
        "lineage_drift",
        "projection_drift",
        "replay_drift_unclassified",
    }
)

_ROUTE_NEEDLES: tuple[str, ...] = (
    "route_kind",
    "resolution_kind",
    "trace.social_contract_trace.route_selected",
    "trace.canonical_entry",
)
_CONTINUITY_NEEDLES: tuple[str, ...] = (
    "continuity",
    "active_interaction",
    "current_interlocutor",
    "dialogue_lock",
)
_SPEAKER_NEEDLES: tuple[str, ...] = (
    "selected_speaker_id",
    "reply_owner",
    "visible_grounded_speaker",
    "speaker",
)
_OWNERSHIP_NEEDLES: tuple[str, ...] = (
    "opening_fallback_owner_bucket",
    "opening_fallback_authorship_source",
    "sealed_fallback_owner_bucket",
    "visibility_fallback_owner_bucket",
    "visibility_fallback_pool",
    "visibility_fallback_kind",
    "visibility_replacement_applied",
)
_FALLBACK_NEEDLES: tuple[str, ...] = (
    "fallback_family",
    "fallback_temporal_frame",
    "final_emitted_source",
    "opening_recovered_via_fallback",
)
_EMISSION_NEEDLES: tuple[str, ...] = (
    "upstream_prepared_emission",
    "prepared_emission_owner",
    "response_type_repair",
    "response_type_required",
    "response_type_candidate",
    "stage_diff",
    "post_gate_mutation",
    "final_emission_mutation_lineage",
    "validator",
)


def _field_matches(field_path: str, needles: tuple[str, ...]) -> bool:
    field_l = field_path.lower()
    return any(needle.lower() in field_l for needle in needles)


def _tag_set(replay_tags: Sequence[str] | None) -> set[str]:
    if not replay_tags:
        return set()
    return {str(tag) for tag in replay_tags if str(tag).strip()}


def classify_owner_drift_bucket(
    *,
    field_path: str,
    category: str,
    measurement_drift_bucket: str,
    replay_tags: Sequence[str] | None,
) -> str:
    """Map one single-run drift row to an owner drift bucket (AR1 priority order)."""
    path = str(field_path or "")
    cat = str(category or "")
    measurement = str(measurement_drift_bucket or "")
    tags = _tag_set(replay_tags)

    if cat == "speaker" or _field_matches(path, _SPEAKER_NEEDLES):
        return "speaker_drift"

    if (
        cat == "route"
        or cat == "continuity"
        or _field_matches(path, _ROUTE_NEEDLES)
        or _field_matches(path, _CONTINUITY_NEEDLES)
    ):
        return "route_drift"

    if _field_matches(path, _OWNERSHIP_NEEDLES):
        return "ownership_drift"

    if cat == "fallback" or _field_matches(path, _FALLBACK_NEEDLES):
        return "fallback_drift"

    if cat in {"emission", "validator", "upstream_prepared_emission"} or _field_matches(path, _EMISSION_NEEDLES):
        return "emission_drift"

    if (
        path == "scaffold_leakage"
        or path.startswith("semantic.")
        or cat in {"sanitizer", "semantic_mutation"}
        or measurement == "semantic_drift"
    ):
        return "semantic_drift"

    if cat in {"projection", "normalization"} or "missing_observation" in tags:
        return "projection_drift"

    if measurement == "exact_drift" or cat in {"replay_drift", "evaluator"}:
        return "replay_drift_unclassified"

    return "replay_drift_unclassified"


def classify_rerun_delta_owner_drift_bucket(
    delta_key: str,
    delta_payload: Mapping[str, Any] | None,
) -> str:
    """Map one rerun per-turn delta key to an owner drift bucket (AR1 priority order)."""
    key = str(delta_key or "")
    payload = delta_payload if isinstance(delta_payload, Mapping) else {}

    if key == "runtime_lineage":
        return "lineage_drift"
    if key == "speaker":
        return "speaker_drift"
    if key == "route":
        return "route_drift"
    if key == "fallback":
        previous_family = payload.get("previous_family")
        current_family = payload.get("current_family")
        if previous_family == current_family:
            return "ownership_drift"
        return "fallback_drift"
    if key == "response_delta":
        return "emission_drift"
    if key == "scaffold":
        return "semantic_drift"
    if key == "text_fingerprint":
        return "replay_drift_unclassified"

    return "replay_drift_unclassified"


def owner_drift_classifications_from_per_turn_deltas(
    per_turn_deltas: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Build scorecard owner drift classification rows from rerun per-turn deltas."""
    rows: list[dict[str, Any]] = []
    for turn_row in per_turn_deltas:
        if not isinstance(turn_row, Mapping):
            continue
        deltas = turn_row.get("deltas")
        if not isinstance(deltas, Mapping):
            continue
        turn_index = turn_row.get("turn_index")
        for delta_key, payload in deltas.items():
            rows.append(
                {
                    "turn_index": turn_index,
                    "owner_drift_bucket": classify_rerun_delta_owner_drift_bucket(
                        str(delta_key),
                        payload if isinstance(payload, Mapping) else {},
                    ),
                    "delta_key": str(delta_key),
                }
            )
    return rows


def summarize_owner_drift_buckets(
    classifications: Sequence[Mapping[str, Any]] | None,
) -> dict[str, int]:
    """Count owner drift bucket occurrences from classification rows."""
    counts = {bucket: 0 for bucket in sorted(ALLOWED_OWNER_DRIFT_BUCKETS)}
    if not classifications:
        return counts
    for row in classifications:
        if not isinstance(row, Mapping):
            continue
        bucket = str(row.get("owner_drift_bucket") or "").strip()
        if bucket in ALLOWED_OWNER_DRIFT_BUCKETS:
            counts[bucket] += 1
    return counts
