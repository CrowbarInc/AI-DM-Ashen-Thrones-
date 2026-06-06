"""Replay-side deterministic failure classification.

The classifier consumes golden replay observation/drift rows and emits
dashboard-ready diagnostics.  It is intentionally read-only: no runtime
systems are imported, called, or mutated here.
"""
from __future__ import annotations

from typing import Any, Mapping, NotRequired, Sequence, TypedDict

from game.final_emission_meta import opening_fallback_owner_bucket_from_meta
from tests.failure_classification_contract import (
    ALLOWED_CLASSIFICATION_ROW_FIELDS,
    ALLOWED_EMISSION_SUBLAYERS,
    ALLOWED_FAILURE_CATEGORIES,
    ALLOWED_FAILURE_SEVERITIES,
    ALLOWED_FALLBACK_CONTENT_OWNERS,
    ALLOWED_FALLBACK_SELECTION_OWNERS,
    ALLOWED_MISSING_SOURCE_KINDS,
    ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS,
    ALLOWED_OWNER_DRIFT_BUCKETS,
    ALLOWED_PRIMARY_OWNERS,
    ALLOWED_REPLAY_TAGS,
    ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS,
    ALLOWED_SECONDARY_OWNERS,
    ALLOWED_SOURCE_FAMILY_TAGS,
    ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS,
    CLASSIFIER_EVIDENCE_FIELDS,
    EXPERIMENTAL_REPLAY_TAG_PREFIX,
    MAJOR_OWNER_INVESTIGATION_TARGETS,
    REQUIRED_CLASSIFICATION_FIELDS,
)
from tests.helpers.replay_drift_taxonomy import classify_owner_drift_bucket


FailureCategory = str
FailureOwner = str
FailureSeverity = str


class FailureClassification(TypedDict):
    scenario_id: str
    turn_index: int
    category: FailureCategory
    severity: FailureSeverity
    primary_owner: FailureOwner
    secondary_owner: NotRequired[FailureOwner | None]
    source_family: str
    replay_tags: list[str]
    field_path: str
    expected: Any
    actual: Any
    reason: str
    final_text_hash: NotRequired[str | None]
    route_kind: NotRequired[Any]
    selected_speaker_id: NotRequired[Any]
    canonical_target_actor_id: NotRequired[Any]
    final_emitted_source: NotRequired[Any]
    final_emission_mutation_lineage: NotRequired[Any]
    fallback_family: NotRequired[Any]
    fallback_temporal_frame: NotRequired[Any]
    opening_fallback_authorship_source: NotRequired[Any]
    opening_fallback_owner_bucket: NotRequired[Any]
    fallback_selection_owner: NotRequired[str | None]
    fallback_content_owner: NotRequired[str | None]
    sealed_fallback_owner_bucket: NotRequired[Any]
    visibility_fallback_owner_bucket: NotRequired[Any]
    visibility_replacement_applied: NotRequired[Any]
    visibility_fallback_pool: NotRequired[Any]
    visibility_fallback_kind: NotRequired[Any]
    upstream_prepared_emission_used: NotRequired[Any]
    upstream_prepared_emission_valid: NotRequired[Any]
    upstream_prepared_emission_source: NotRequired[Any]
    upstream_prepared_emission_reject_reason: NotRequired[Any]
    prepared_emission_owner: NotRequired[str | None]
    response_type_required: NotRequired[Any]
    response_type_repair_used: NotRequired[Any]
    response_type_repair_kind: NotRequired[Any]
    post_gate_mutation_detected: NotRequired[Any]
    emission_sublayer: NotRequired[str | None]
    repair_kind: NotRequired[str | None]
    mutation_source: NotRequired[str | None]
    missing_source_kind: NotRequired[str | None]
    sanitizer_mode: NotRequired[Any]
    sanitizer_event_count: NotRequired[Any]
    sanitizer_changed_count: NotRequired[Any]
    sanitizer_rewrite_used: NotRequired[Any]
    sanitizer_empty_fallback_used: NotRequired[Any]
    sanitizer_empty_fallback_source: NotRequired[Any]
    sanitizer_empty_fallback_owner: NotRequired[str | None]
    sanitizer_lineage_mode: NotRequired[Any]
    sanitizer_lineage_changed_count: NotRequired[Any]
    sanitizer_lineage_dropped_count: NotRequired[Any]
    sanitizer_lineage_empty_fallback_used: NotRequired[Any]
    sanitizer_lineage_legacy_rewrite_active: NotRequired[Any]
    sanitizer_strict_social_fallback_used: NotRequired[Any]
    sanitizer_strict_social_selection_owner: NotRequired[str | None]
    sanitizer_strict_social_prose_owner: NotRequired[str | None]
    sanitizer_strict_social_source: NotRequired[Any]
    unavailable_fields: list[str]
    raw_signal_refs: list[str]
    classification_confidence: str
    investigate_first: str
    owner_drift_bucket: NotRequired[str]


CATEGORY_RULES: tuple[tuple[str, tuple[str, ...], FailureCategory, str], ...] = (
    ("exact_drift", ("final_text",), "replay_drift", "golden_replay_projection"),
    ("scaffold_leakage", ("scaffold_leakage",), "sanitizer", "output_sanitizer"),
    ("route", ("route_kind", "resolution_kind", "trace.social_contract_trace.route_selected"), "route", "interaction_context"),
    ("continuity", ("continuity", "active_interaction", "current_interlocutor", "dialogue_lock"), "continuity", "interaction_continuity"),
    ("speaker", ("selected_speaker_id", "reply_owner", "visible_grounded_speaker", "speaker"), "speaker", "speaker_contract"),
    ("opening_fallback", ("opening_recovered_via_fallback", "opening_fallback_authorship_source", "opening_fallback_owner_bucket"), "fallback", "opening_fallback"),
    ("fallback", ("fallback_family", "fallback_temporal_frame", "sealed_fallback_owner_bucket", "visibility_fallback_owner_bucket", "visibility_fallback_pool", "visibility_fallback_kind"), "fallback", "fallback_behavior"),
    ("fallback_source", ("final_emitted_source",), "fallback", "final_emission_gate"),
    ("upstream_prepared_emission", ("upstream_prepared_emission", "prepared_emission_owner"), "emission", "upstream_prepared_emission"),
    ("response_type_repair", ("response_type_repair_used", "response_type_repair_kind"), "emission", "final_emission_gate"),
    ("response_type", ("response_type_required", "response_type_candidate_ok", "validator"), "validator", "response_type"),
    ("stage_diff", ("stage_diff", "post_gate_mutation_detected"), "emission", "stage_diff"),
    ("sanitizer_strict_social_fallback", ("sanitizer_strict_social_fallback",), "sanitizer", "output_sanitizer"),
    ("sanitizer_empty_fallback", ("sanitizer_empty_fallback",), "sanitizer", "output_sanitizer"),
    ("normalization", ("normalization", "normalized", "schema_contract"), "normalization", "schema_contracts"),
    ("projection", ("unavailable", "missing_observation"), "projection", "golden_replay_projection"),
    ("evaluator", ("evaluator", "score", "warning"), "evaluator", "behavioral_eval"),
    ("semantic_text", ("semantic.", "semantic_drift", "final_text"), "semantic_mutation", "stage_diff"),
)

# Cycle F.I policy note: opening-fallback fields keep the coarse ``fallback``
# taxonomy where possible, while ``investigate_first`` can route by symptom.
# Gate selection/final source/fail-closed/FEM merge stay gate-owned; composition/basis routes to
# ``game/opening_deterministic_fallback.py``; upstream payload issues to
# ``game/upstream_response_repairs.py``; owner-bucket mapping to ``game/final_emission_meta.py``;
# replay projection to ``tests/helpers/golden_replay.py``; classifier policy here; dashboard
# rendering to ``tests/helpers/failure_dashboard_report.py``.
PRIMARY_OWNER_RULES: dict[FailureCategory, FailureOwner] = {
    "route": "route",
    "speaker": "speaker",
    "fallback": "fallback",
    "emission": "emission",
    "semantic_mutation": "semantic_mutation",
    "replay_drift": "replay",
    "projection": "projection",
    "validator": "validator",
    "evaluator": "evaluator",
    "continuity": "continuity",
    "normalization": "normalization",
    "sanitizer": "sanitizer",
    "upstream_prepared_emission": "upstream_prepared_emission",
}

SECONDARY_OWNER_RULES: dict[FailureCategory, FailureOwner | None] = {
    "route": "projection",
    "speaker": "emission",
    "fallback": "emission",
    "emission": "validator",
    "semantic_mutation": "emission",
    "replay_drift": "emission",
    "projection": None,
    "validator": "emission",
    "evaluator": None,
    "continuity": "route",
    "normalization": "projection",
    "sanitizer": "emission",
    "upstream_prepared_emission": "emission",
}

INVESTIGATION_TARGETS: dict[FailureCategory, str] = {
    "route": "game/interaction_context.py",
    "speaker": "game/speaker_contract_enforcement.py",
    "fallback": "game/final_emission_gate.py",
    "emission": "game/final_emission_gate.py",
    "semantic_mutation": "game/stage_diff_telemetry.py",
    "replay_drift": "tests/helpers/golden_replay.py",
    "projection": "tests/helpers/golden_replay.py",
    "validator": "game/final_emission_validators.py",
    "evaluator": "game/scenario_spine_eval.py",
    "continuity": "game/interaction_context.py",
    "normalization": "game/final_emission_meta.py",
    "sanitizer": "game/output_sanitizer.py",
    "upstream_prepared_emission": "game/final_emission_gate.py",
}

# Contract ↔ classifier alignment is enforced by tests.helpers.failure_classification_sync.

FIELD_TARGET_OVERRIDES: tuple[tuple[str, str], ...] = (
    ("response_type_repair", "game/final_emission_gate.py"),
    ("response_type", "game/final_emission_validators.py"),
    ("final_emitted_source", "game/final_emission_gate.py"),
    ("fallback", "game/final_emission_gate.py"),
    ("speaker", "game/speaker_contract_enforcement.py"),
    ("route", "game/interaction_context.py"),
    ("trace.canonical_entry", "game/interaction_context.py"),
)

FALLBACK_SOURCE_MARKERS = (
    "fallback",
    "terminal",
    "emergency",
    "safe",
    "strict_social",
    "opening",
)

POST_GATE_LINEAGE_SOURCE_MAP: dict[str, str] = {
    "sanitizer_empty_fallback": "sanitizer.empty_fallback",
    "pre_gate_sanitizer": "sanitizer",
    "response_type_repair": "response_type",
    "prepared_emission_selection": "upstream_prepared_emission",
    "opening_fallback_selection": "opening_fallback",
    "fallback_behavior_repair": "fallback_behavior",
    "sealed_fallback_replacement": "sealed_gate",
    "finalize_html_strip": "final_emission.finalize_packaging",
    "finalize_route_illegal_strip": "final_emission.finalize_route_illegal_strip",
    "finalize_packaging": "final_emission.finalize_packaging",
}

POST_GATE_LINEAGE_SOURCE_PRIORITY: tuple[str, ...] = (
    "sanitizer_empty_fallback",
    "finalize_route_illegal_strip",
    "response_type_repair",
    "prepared_emission_selection",
    "opening_fallback_selection",
    "fallback_behavior_repair",
    "sealed_fallback_replacement",
    "pre_gate_sanitizer",
    "finalize_html_strip",
    "finalize_packaging",
)

_CLASSIFIER_COMPUTED_EVIDENCE_FIELDS: frozenset[str] = frozenset(
    {
        "canonical_target_actor_id",
        "emission_sublayer",
        "fallback_content_owner",
        "fallback_selection_owner",
        "final_text_hash",
        "missing_source_kind",
        "mutation_source",
        "opening_fallback_owner_bucket",
        "prepared_emission_owner",
        "repair_kind",
        "secondary_owner",
    }
)

# Manifest fields copied from ``observed_turn`` via ``Mapping.get`` (not computed).
_CLASSIFIER_MANIFEST_DIRECT_OBSERVED_FIELDS: frozenset[str] = (
    CLASSIFIER_EVIDENCE_FIELDS - _CLASSIFIER_COMPUTED_EVIDENCE_FIELDS
)

if _CLASSIFIER_MANIFEST_DIRECT_OBSERVED_FIELDS | _CLASSIFIER_COMPUTED_EVIDENCE_FIELDS != CLASSIFIER_EVIDENCE_FIELDS:
    raise AssertionError("classifier evidence manifest direct/computed partition must cover all evidence fields")


def _copy_manifest_observed_evidence(
    row: dict[str, Any],
    observed_turn: Mapping[str, Any],
    *,
    fields: frozenset[str] = _CLASSIFIER_MANIFEST_DIRECT_OBSERVED_FIELDS,
) -> None:
    """Copy optional evidence keys from the observed turn using the AK2 manifest."""
    for field in fields:
        row[field] = observed_turn.get(field)


def _lookup_path(obj: Mapping[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in str(path or "").split("."):
        if not part:
            return None
        if not isinstance(cur, Mapping) or part not in cur:
            return None
        cur = cur.get(part)
    return cur


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple, set, frozenset)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def _lineage_tokens(value: Any) -> list[str]:
    return [str(item).strip().lower() for item in _as_list(value) if str(item).strip()]


def _post_gate_lineage_mutation_source(observed_turn: Mapping[str, Any]) -> str | None:
    if observed_turn.get("post_gate_mutation_detected") is not True:
        return None
    tokens = set(_lineage_tokens(observed_turn.get("final_emission_mutation_lineage")))
    if not tokens:
        return None
    for token in POST_GATE_LINEAGE_SOURCE_PRIORITY:
        if token in tokens:
            return POST_GATE_LINEAGE_SOURCE_MAP[token]
    return None


def validate_failure_classification_row(row: Mapping[str, Any]) -> list[str]:
    """Validate one failure classification row against the dashboard contract."""
    errors: list[str] = []
    for field in sorted(REQUIRED_CLASSIFICATION_FIELDS - set(row.keys())):
        errors.append(f"missing required field: {field}")

    category = row.get("category")
    if category not in ALLOWED_FAILURE_CATEGORIES:
        errors.append(f"invalid category: {category!r}")

    severity = row.get("severity")
    if severity not in ALLOWED_FAILURE_SEVERITIES:
        errors.append(f"invalid severity: {severity!r}")

    primary_owner = row.get("primary_owner")
    if primary_owner not in ALLOWED_PRIMARY_OWNERS:
        errors.append(f"invalid primary_owner: {primary_owner!r}")

    secondary_owner = row.get("secondary_owner")
    if secondary_owner not in (None, "") and secondary_owner not in ALLOWED_SECONDARY_OWNERS:
        errors.append(f"invalid secondary_owner: {secondary_owner!r}")

    source_family = row.get("source_family")
    if source_family not in ALLOWED_SOURCE_FAMILY_TAGS:
        errors.append(f"invalid source_family: {source_family!r}")

    replay_tags = row.get("replay_tags")
    if not isinstance(replay_tags, list):
        errors.append("replay_tags must be a list")
    else:
        for tag in replay_tags:
            tag_s = str(tag)
            if tag_s not in ALLOWED_REPLAY_TAGS and not tag_s.startswith(EXPERIMENTAL_REPLAY_TAG_PREFIX):
                errors.append(f"invalid replay_tag: {tag_s!r}")

    if not isinstance(row.get("unavailable_fields"), list):
        errors.append("unavailable_fields must be a list")
    if not isinstance(row.get("raw_signal_refs"), list):
        errors.append("raw_signal_refs must be a list")

    field_path = row.get("field_path")
    if not isinstance(field_path, str) or not field_path.strip():
        errors.append("field_path must be a non-empty string")

    investigate_first = row.get("investigate_first")
    if not isinstance(investigate_first, str) or not investigate_first.strip():
        errors.append("investigate_first must be a non-empty string")

    missing_source_kind = row.get("missing_source_kind")
    if missing_source_kind not in (None, "") and missing_source_kind not in ALLOWED_MISSING_SOURCE_KINDS:
        errors.append(f"invalid missing_source_kind: {missing_source_kind!r}")

    emission_sublayer = row.get("emission_sublayer")
    if emission_sublayer not in (None, "") and emission_sublayer not in ALLOWED_EMISSION_SUBLAYERS:
        errors.append(f"invalid emission_sublayer: {emission_sublayer!r}")

    opening_bucket = row.get("opening_fallback_owner_bucket")
    if opening_bucket not in (None, "") and opening_bucket not in ALLOWED_OPENING_FALLBACK_OWNER_BUCKETS:
        errors.append(f"invalid opening_fallback_owner_bucket: {opening_bucket!r}")

    sealed_bucket = row.get("sealed_fallback_owner_bucket")
    if sealed_bucket not in (None, "") and sealed_bucket not in ALLOWED_SEALED_FALLBACK_OWNER_BUCKETS:
        errors.append(f"invalid sealed_fallback_owner_bucket: {sealed_bucket!r}")

    visibility_bucket = row.get("visibility_fallback_owner_bucket")
    if visibility_bucket not in (None, "") and visibility_bucket not in ALLOWED_VISIBILITY_FALLBACK_OWNER_BUCKETS:
        errors.append(f"invalid visibility_fallback_owner_bucket: {visibility_bucket!r}")

    fallback_selection_owner = row.get("fallback_selection_owner")
    if fallback_selection_owner not in (None, "") and fallback_selection_owner not in ALLOWED_FALLBACK_SELECTION_OWNERS:
        errors.append(f"invalid fallback_selection_owner: {fallback_selection_owner!r}")

    fallback_content_owner = row.get("fallback_content_owner")
    if fallback_content_owner not in (None, "") and fallback_content_owner not in ALLOWED_FALLBACK_CONTENT_OWNERS:
        errors.append(f"invalid fallback_content_owner: {fallback_content_owner!r}")

    prepared_owner = row.get("prepared_emission_owner")
    if prepared_owner not in (None, "") and prepared_owner != "upstream_prepared_emission":
        errors.append(f"invalid prepared_emission_owner: {prepared_owner!r}")

    sanitizer_empty_owner = row.get("sanitizer_empty_fallback_owner")
    if sanitizer_empty_owner not in (None, "") and sanitizer_empty_owner != "output_sanitizer":
        errors.append(f"invalid sanitizer_empty_fallback_owner: {sanitizer_empty_owner!r}")

    strict_social_selection_owner = row.get("sanitizer_strict_social_selection_owner")
    if strict_social_selection_owner not in (None, "") and strict_social_selection_owner != "output_sanitizer":
        errors.append(f"invalid sanitizer_strict_social_selection_owner: {strict_social_selection_owner!r}")

    strict_social_prose_owner = row.get("sanitizer_strict_social_prose_owner")
    if strict_social_prose_owner not in (None, "") and strict_social_prose_owner != "strict_social_emission":
        errors.append(f"invalid sanitizer_strict_social_prose_owner: {strict_social_prose_owner!r}")

    owner_drift_bucket = row.get("owner_drift_bucket")
    if owner_drift_bucket not in (None, "") and owner_drift_bucket not in ALLOWED_OWNER_DRIFT_BUCKETS:
        errors.append(f"invalid owner_drift_bucket: {owner_drift_bucket!r}")

    for key in sorted(row.keys()):
        if key not in ALLOWED_CLASSIFICATION_ROW_FIELDS:
            errors.append(f"unknown classification field: {key}")

    return errors


def _field_matches(field_path: str, needles: tuple[str, ...]) -> bool:
    field_l = field_path.lower()
    return any(needle.lower() in field_l for needle in needles)


def _drift_bucket(row: Mapping[str, Any]) -> str:
    for key in ("drift_bucket", "bucket", "drift_type"):
        if row.get(key):
            return str(row[key])
    tags = _as_list(row.get("replay_tags"))
    for tag in ("exact_drift", "semantic_drift", "structural_drift"):
        if tag in tags:
            return tag
    return ""


def _canonical_target_actor_id(observed_turn: Mapping[str, Any]) -> Any:
    return _lookup_path(observed_turn, "trace.canonical_entry.target_actor_id") or _lookup_path(
        observed_turn, "trace.canonical_entry_target_actor_id"
    )


def _missing_source_kind(field_path: str, observed_turn: Mapping[str, Any], drift_row: Mapping[str, Any]) -> str | None:
    explicit = drift_row.get("missing_source_kind") or _lookup_path(observed_turn, f"missing_source_by_field.{field_path}")
    if explicit:
        return str(explicit)
    unavailable = set(_as_list(observed_turn.get("unavailable"))) | set(_as_list(drift_row.get("unavailable_fields")))
    if field_path not in unavailable and drift_row.get("reason") != "unexpected unavailable field":
        return None
    raw_presence = observed_turn.get("raw_signal_presence") if isinstance(observed_turn.get("raw_signal_presence"), Mapping) else {}
    raw_present = raw_presence.get(field_path)
    normalized_presence = (
        observed_turn.get("normalized_signal_presence")
        if isinstance(observed_turn.get("normalized_signal_presence"), Mapping)
        else {}
    )
    normalized_present = normalized_presence.get(field_path)
    if raw_present is True and normalized_present is False:
        return "normalized_view_missing_raw_present"
    if raw_present is True:
        return "projection_missing_raw_present"
    if raw_present is False:
        return "runtime_missing_raw_absent"
    return "unknown_missing_source"


def _route_metadata_missing(field_path: str, observed_turn: Mapping[str, Any], drift_row: Mapping[str, Any]) -> bool:
    unavailable = set(_as_list(observed_turn.get("unavailable"))) | set(_as_list(drift_row.get("unavailable_fields")))
    route_fields = {"route_kind", "trace.social_contract_trace", "trace.turn_trace"}
    return field_path in route_fields and (field_path in unavailable or drift_row.get("actual") is None)


def _emission_sublayer(observed_turn: Mapping[str, Any], drift_row: Mapping[str, Any]) -> str | None:
    field_path = str(drift_row.get("field_path") or "")
    final_source = str(observed_turn.get("final_emitted_source") or drift_row.get("actual") or "").lower()
    repair_kind = str(observed_turn.get("response_type_repair_kind") or drift_row.get("repair_kind") or "").lower()
    fallback_family = str(observed_turn.get("fallback_family") or "").lower()
    stage_diff = observed_turn.get("stage_diff") if isinstance(observed_turn.get("stage_diff"), Mapping) else {}
    repair_flags = set(_as_list(observed_turn.get("stage_diff_repair_flags")))
    for snap in _as_list(stage_diff.get("snapshots")):
        if isinstance(snap, Mapping):
            repair_flags.update(_as_list(snap.get("repair_flags")))

    if _prepared_emission_owner(observed_turn) == "upstream_prepared_emission":
        return "upstream_prepared_emission"
    if observed_turn.get("sanitizer_strict_social_fallback_used") is True:
        return "strict_social_replacement"
    if field_path.startswith("response_type") or observed_turn.get("response_type_repair_used") is True:
        return "response_type"
    if observed_turn.get("opening_recovered_via_fallback") or "opening" in final_source or "opening" in repair_kind:
        return "opening_fallback"
    if observed_turn.get("fallback_behavior_repaired") or "fallback_behavior_repaired" in repair_flags:
        return "fallback_behavior"
    if observed_turn.get("strict_social_active") or "strict_social" in final_source or "strict_social" in repair_kind:
        return "strict_social_replacement"
    if observed_turn.get("speaker_contract_enforcement_reason") or "speaker_contract" in final_source:
        return "speaker_contract_enforcement"
    if "interaction_continuity" in final_source or "interaction_continuity" in repair_kind:
        return "interaction_continuity"
    if (
        observed_turn.get("sanitizer_rewrite_used")
        or observed_turn.get("sanitizer_event_count")
        or bool(observed_turn.get("sanitizer_lineage_changed_count"))
        or observed_turn.get("sanitizer_lineage_empty_fallback_used") is True
        or observed_turn.get("sanitizer_empty_fallback_used") is True
    ):
        return "sanitizer"
    if "terminal" in final_source or "emergency_fallback" in final_source or "global_scene_fallback" in final_source:
        return "terminal_fallback"
    if observed_turn.get("post_gate_mutation_detected") is True:
        return _post_gate_lineage_mutation_source(observed_turn) or "emission.post_gate_mutation_unknown"
    if fallback_family:
        return "fallback_behavior"
    return None


def _has_prepared_emission_telemetry(observed_turn: Mapping[str, Any]) -> bool:
    return any(
        key in observed_turn
        for key in (
            "upstream_prepared_emission_used",
            "upstream_prepared_emission_valid",
            "upstream_prepared_emission_source",
            "upstream_prepared_emission_reject_reason",
        )
    )


def _prepared_emission_owner(observed_turn: Mapping[str, Any]) -> str | None:
    if not _has_prepared_emission_telemetry(observed_turn):
        return None
    if observed_turn.get("upstream_prepared_emission_used") is True:
        return "upstream_prepared_emission"
    return None


def _prepared_emission_source_family(observed_turn: Mapping[str, Any], source_family: str) -> str:
    if _prepared_emission_owner(observed_turn) == "upstream_prepared_emission":
        return "upstream_prepared_emission"
    return source_family


def _opening_fallback_evidence_present(observed_turn: Mapping[str, Any], drift_row: Mapping[str, Any]) -> bool:
    field_path = str(drift_row.get("field_path") or "").lower()
    final_source = str(observed_turn.get("final_emitted_source") or drift_row.get("actual") or "").lower()
    repair_kind = str(observed_turn.get("response_type_repair_kind") or drift_row.get("repair_kind") or "").lower()
    fallback_family = str(observed_turn.get("fallback_family") or "").lower()
    return (
        observed_turn.get("opening_recovered_via_fallback") is True
        or bool(str(observed_turn.get("opening_fallback_authorship_source") or "").strip())
        or bool(str(observed_turn.get("opening_fallback_owner_bucket") or "").strip())
        or fallback_family == "scene_opening"
        or "opening" in field_path
        or "opening" in final_source
        or "opening" in repair_kind
    )


def _opening_fallback_owner_bucket(observed_turn: Mapping[str, Any], drift_row: Mapping[str, Any]) -> str | None:
    observed = observed_turn.get("opening_fallback_owner_bucket")
    if isinstance(observed, str) and observed.strip():
        return observed.strip()
    if not _opening_fallback_evidence_present(observed_turn, drift_row):
        return None
    mapped = opening_fallback_owner_bucket_from_meta(observed_turn)
    return mapped if isinstance(mapped, str) and mapped.strip() else None


def _fallback_split_owner(observed_turn: Mapping[str, Any], owner_field: str) -> str | None:
    raw_events = observed_turn.get("runtime_lineage_events")
    events = raw_events if isinstance(raw_events, Sequence) and not isinstance(raw_events, (str, bytes)) else ()
    for event in events:
        if not isinstance(event, Mapping):
            continue
        if event.get("event_kind") != "fallback_selected":
            continue
        value = event.get(owner_field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    value = observed_turn.get(owner_field)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _repair_kind(observed_turn: Mapping[str, Any], drift_row: Mapping[str, Any]) -> str | None:
    for value in (
        observed_turn.get("response_type_repair_kind"),
        observed_turn.get("fallback_behavior_repair_kind"),
        observed_turn.get("narrative_authenticity_repair_mode"),
        drift_row.get("repair_kind"),
    ):
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _mutation_source(observed_turn: Mapping[str, Any], emission_sublayer: str | None) -> str | None:
    if emission_sublayer:
        return emission_sublayer
    if observed_turn.get("post_gate_mutation_detected") is True:
        return _post_gate_lineage_mutation_source(observed_turn) or "emission.post_gate_mutation_unknown"
    return None


def _fallback_observed(observed_turn: Mapping[str, Any], drift_row: Mapping[str, Any]) -> bool:
    values = [
        observed_turn.get("fallback_family"),
        observed_turn.get("final_emitted_source"),
        observed_turn.get("opening_fallback_authorship_source"),
        observed_turn.get("opening_fallback_owner_bucket"),
        observed_turn.get("sealed_fallback_owner_bucket"),
        observed_turn.get("visibility_fallback_owner_bucket"),
        observed_turn.get("visibility_replacement_applied"),
        observed_turn.get("visibility_fallback_pool"),
        observed_turn.get("visibility_fallback_kind"),
        drift_row.get("actual"),
    ]
    return any(any(marker in str(value).lower() for marker in FALLBACK_SOURCE_MARKERS) for value in values if value is not None)


def _replay_tags(
    *,
    category: FailureCategory,
    field_path: str,
    observed_turn: Mapping[str, Any],
    drift_row: Mapping[str, Any],
) -> list[str]:
    tags = set(_as_list(drift_row.get("replay_tags")))
    bucket = _drift_bucket(drift_row)
    if bucket:
        tags.add(bucket)
    if drift_row.get("reason") == "unexpected unavailable field" or field_path in set(_as_list(observed_turn.get("unavailable"))):
        tags.add("missing_observation")
    if category == "route":
        tags.add("route_mismatch" if not _route_metadata_missing(field_path, observed_turn, drift_row) else "missing_route_metadata")
    elif category == "speaker":
        tags.add("speaker_mismatch")
    elif category == "fallback":
        tags.add("fallback_source_mismatch" if field_path == "final_emitted_source" else "fallback_family_mismatch")
    elif category == "sanitizer":
        tags.add("scaffold_leakage")
    elif category == "continuity":
        tags.add("continuity_break")
    elif category == "semantic_mutation":
        tags.add("semantic_mutation")
    elif category == "emission" and field_path.startswith("response_type_repair"):
        tags.add("response_type_repair_mismatch")
    elif category == "evaluator":
        tags.add("evaluator_warning" if "warning" in str(drift_row.get("reason") or "").lower() else "evaluator_failure")
    return sorted(tags)


def classify_failure_category(
    *,
    observed_turn: Mapping[str, Any],
    drift_row: Mapping[str, Any],
) -> FailureCategory:
    field_path = str(drift_row.get("field_path") or "")
    bucket = _drift_bucket(drift_row)
    reason = str(drift_row.get("reason") or "").lower()

    if bucket == "exact_drift":
        return "replay_drift"
    if field_path == "scaffold_leakage":
        return "sanitizer"
    missing_kind = _missing_source_kind(field_path, observed_turn, drift_row)
    if missing_kind in {"projection_missing_raw_present", "normalized_view_missing_raw_present"}:
        return "normalization" if missing_kind == "normalized_view_missing_raw_present" else "projection"
    if _route_metadata_missing(field_path, observed_turn, drift_row):
        return "route"
    if field_path == "final_emitted_source" and _fallback_observed(observed_turn, drift_row):
        return "fallback"
    if bucket == "semantic_drift" and field_path == "final_text":
        return "semantic_mutation"
    if "unavailable" in reason and field_path.startswith("trace."):
        return "projection"

    for _name, needles, category, _source_family in CATEGORY_RULES:
        if _field_matches(field_path, needles):
            return category
    return "replay_drift"


def determine_primary_owner(
    *,
    category: FailureCategory,
    observed_turn: Mapping[str, Any] | None = None,
    drift_row: Mapping[str, Any] | None = None,
) -> FailureOwner:
    missing_kind = _missing_source_kind(str((drift_row or {}).get("field_path") or ""), observed_turn or {}, drift_row or {})
    prepared_owner = _prepared_emission_owner(observed_turn or {})
    if prepared_owner:
        return prepared_owner
    if missing_kind == "projection_missing_raw_present":
        return "projection"
    if missing_kind == "normalized_view_missing_raw_present":
        return "normalization"
    if missing_kind == "runtime_missing_raw_absent" and category == "projection":
        return "route"
    return PRIMARY_OWNER_RULES.get(category, "replay")


def determine_secondary_owner(
    *,
    category: FailureCategory,
    observed_turn: Mapping[str, Any] | None = None,
    drift_row: Mapping[str, Any] | None = None,
) -> FailureOwner | None:
    field_path = str((drift_row or {}).get("field_path") or "")
    missing_kind = _missing_source_kind(field_path, observed_turn or {}, drift_row or {})
    if _prepared_emission_owner(observed_turn or {}):
        return "emission"
    if missing_kind == "projection_missing_raw_present":
        return None
    if missing_kind == "normalized_view_missing_raw_present":
        return "projection"
    if missing_kind == "runtime_missing_raw_absent" and category in {"route", "projection"}:
        return "projection"
    if category == "route" and _route_metadata_missing(field_path, observed_turn or {}, drift_row or {}):
        return "projection"
    if category == "projection" and field_path in {"route_kind", "trace.social_contract_trace"}:
        return "route"
    return SECONDARY_OWNER_RULES.get(category)


def classify_failure_severity(
    *,
    category: FailureCategory,
    observed_turn: Mapping[str, Any],
    drift_row: Mapping[str, Any],
    replay_tags: Sequence[str] = (),
) -> FailureSeverity:
    field_path = str(drift_row.get("field_path") or "")
    tags = set(replay_tags)
    if category in {"sanitizer", "semantic_mutation"}:
        return "critical"
    if category == "speaker":
        return "critical" if observed_turn.get("route_kind") in {"dialogue", "social"} else "high"
    if category == "route":
        return "high" if not _route_metadata_missing(field_path, observed_turn, drift_row) else "medium"
    if category == "fallback":
        return "high"
    if category == "validator":
        return "high"
    if category == "emission":
        return "medium" if "response_type_repair_mismatch" in tags else "high"
    if category == "continuity":
        return "high"
    if category == "projection":
        return "medium"
    if _missing_source_kind(field_path, observed_turn, drift_row) == "runtime_missing_raw_absent":
        return "medium"
    if category == "evaluator":
        return "low" if "evaluator_warning" in tags else "medium"
    if category == "normalization":
        return "low"
    return "low" if _drift_bucket(drift_row) == "exact_drift" else "medium"


# Symptom routing for ``investigate_first`` only: substring markers on ``field_path``,
# not a second copy of :data:`game.final_emission_meta.OPENING_FALLBACK_PROJECTION_FIELDS`.
# Full FEM/replay field registry and owner-bucket mapping stay in ``game.final_emission_meta``.
_OPENING_COMPOSITION_FIELD_MARKERS: tuple[str, ...] = (
    "opening_final_fallback_basis",
    "opening_final_basis_matches_selector",
    "opening_fallback_basis_count",
    "opening_fallback_context",
    "opening_curated_facts",
    "opening_selector",
    "prepared_opening_fallback_text",
)

_OPENING_UPSTREAM_PAYLOAD_FIELD_MARKERS: tuple[str, ...] = (
    "upstream_prepared_opening_fallback",
    "opening_fallback_authorship_source",
    "opening_upstream_prepare",
)

_OPENING_GATE_FIELD_MARKERS: tuple[str, ...] = (
    "final_emitted_source",
    "opening_recovered_via_fallback",
    "scene_opening_accepted_candidate",
    "response_type",
)


def _opening_fallback_investigation_target(
    *,
    observed_turn: Mapping[str, Any],
    drift_row: Mapping[str, Any],
) -> str | None:
    field_path = str(drift_row.get("field_path") or "")
    field_l = field_path.lower()
    if not _opening_fallback_evidence_present(observed_turn, drift_row):
        return None

    missing_kind = _missing_source_kind(field_path, observed_turn, drift_row)
    if missing_kind == "projection_missing_raw_present":
        return "tests/helpers/golden_replay.py"
    if field_l == "opening_fallback_owner_bucket":
        return "game/final_emission_meta.py"
    if any(marker in field_l for marker in _OPENING_GATE_FIELD_MARKERS):
        return "game/final_emission_gate.py"
    if any(marker in field_l for marker in _OPENING_UPSTREAM_PAYLOAD_FIELD_MARKERS):
        return "game/upstream_response_repairs.py"
    if any(marker in field_l for marker in _OPENING_COMPOSITION_FIELD_MARKERS):
        return "game/opening_deterministic_fallback.py"
    return None


def build_investigation_target(
    *,
    category: FailureCategory,
    source_family: str | None = None,
    observed_turn: Mapping[str, Any] | None = None,
    drift_row: Mapping[str, Any] | None = None,
) -> str:
    field_path = str((drift_row or {}).get("field_path") or "")
    opening_target = _opening_fallback_investigation_target(
        observed_turn=observed_turn or {},
        drift_row=drift_row or {},
    )
    if opening_target:
        return opening_target
    if category not in {"sanitizer", "projection", "replay_drift", "semantic_mutation", "normalization"}:
        for needle, target in FIELD_TARGET_OVERRIDES:
            if needle in field_path:
                return target
    return INVESTIGATION_TARGETS.get(category, "tests/helpers/golden_replay.py")


def _source_family_for(category: FailureCategory, field_path: str) -> str:
    for _name, needles, rule_category, source_family in CATEGORY_RULES:
        if category == rule_category and _field_matches(field_path, needles):
            return source_family
    if category == "sanitizer":
        return "output_sanitizer"
    return "golden_replay_projection"


def _raw_signal_refs(field_path: str, observed_turn: Mapping[str, Any]) -> list[str]:
    refs: set[str] = set()
    if field_path.startswith("trace."):
        refs.add("trace")
    if any(
        part in field_path
        for part in ("final_emitted_source", "fallback", "response_type", "opening_", "post_gate", "upstream_prepared_emission")
    ):
        refs.add("_final_emission_meta")
    if field_path.startswith("sanitizer_"):
        refs.add("sanitizer_trace")
    if field_path in set(_as_list(observed_turn.get("unavailable"))):
        refs.add("unavailable")
    if field_path.startswith("selected_speaker") or "speaker" in field_path:
        refs.add("trace.social_contract_trace")
    return sorted(refs)


def classify_replay_failure(
    *,
    scenario_id: str,
    turn_index: int,
    observed_turn: Mapping[str, Any],
    drift_rows: Sequence[Mapping[str, Any]],
) -> list[FailureClassification]:
    classifications: list[FailureClassification] = []
    for drift_row in drift_rows:
        field_path = str(drift_row.get("field_path") or "")
        category = classify_failure_category(observed_turn=observed_turn, drift_row=drift_row)
        source_family = _prepared_emission_source_family(observed_turn, _source_family_for(category, field_path))
        replay_tags = _replay_tags(
            category=category,
            field_path=field_path,
            observed_turn=observed_turn,
            drift_row=drift_row,
        )
        severity = classify_failure_severity(
            category=category,
            observed_turn=observed_turn,
            drift_row=drift_row,
            replay_tags=replay_tags,
        )
        emission_sublayer = _emission_sublayer(observed_turn, drift_row)
        repair_kind = _repair_kind(observed_turn, drift_row)
        missing_source_kind = _missing_source_kind(field_path, observed_turn, drift_row)
        row: FailureClassification = {
            "scenario_id": str(scenario_id),
            "turn_index": int(turn_index or 0),
            "category": category,
            "severity": severity,
            "primary_owner": determine_primary_owner(category=category, observed_turn=observed_turn, drift_row=drift_row),
            "source_family": source_family,
            "replay_tags": replay_tags,
            "field_path": field_path,
            "expected": drift_row.get("expected"),
            "actual": drift_row.get("actual"),
            "reason": str(drift_row.get("reason") or ""),
            "unavailable_fields": sorted(set(_as_list(observed_turn.get("unavailable"))) | set(_as_list(drift_row.get("unavailable_fields")))),
            "raw_signal_refs": _raw_signal_refs(field_path, observed_turn),
            "classification_confidence": "high" if category not in {"projection", "replay_drift"} else "medium",
            "investigate_first": build_investigation_target(
                category=category,
                source_family=source_family,
                observed_turn=observed_turn,
                drift_row=drift_row,
            ),
        }
        _copy_manifest_observed_evidence(row, observed_turn)
        row["secondary_owner"] = determine_secondary_owner(
            category=category, observed_turn=observed_turn, drift_row=drift_row
        )
        row["final_text_hash"] = str(drift_row.get("observed_text_hash") or observed_turn.get("final_text_hash") or "")
        row["canonical_target_actor_id"] = _canonical_target_actor_id(observed_turn)
        row["opening_fallback_owner_bucket"] = _opening_fallback_owner_bucket(observed_turn, drift_row)
        row["fallback_selection_owner"] = _fallback_split_owner(observed_turn, "fallback_selection_owner")
        row["fallback_content_owner"] = _fallback_split_owner(observed_turn, "fallback_content_owner")
        row["prepared_emission_owner"] = _prepared_emission_owner(observed_turn)
        row["emission_sublayer"] = emission_sublayer
        row["repair_kind"] = repair_kind
        row["mutation_source"] = _mutation_source(observed_turn, emission_sublayer)
        row["missing_source_kind"] = missing_source_kind
        row["owner_drift_bucket"] = classify_owner_drift_bucket(
            field_path=field_path,
            category=category,
            measurement_drift_bucket=_drift_bucket(drift_row),
            replay_tags=replay_tags,
        )
        classifications.append(row)
    return classifications
