"""Read-side canonical replacement attribution inventory (BS1).

Consumes existing FEM metadata, runtime lineage events, golden replay projection
rows, and failure classification output without modifying runtime behavior.

**Authority (CG-5):** record construction and completeness metrics only.
Taxonomy unions, paths, and validators are imported from
``tests.helpers.attribution_contract`` (does not own vocabulary).

The five-field completeness contract mirrors
``docs/BS_semantic_replacement_attribution_discovery.md`` Section D.
Registry: ``docs/audits/CG_attribution_contract_registry.md``
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NotRequired, Sequence, TypedDict

from game.attribution_read_views import (
    opening_fallback_owner_bucket_from_meta,
    sealed_fallback_owner_bucket_from_fields,
    visibility_fallback_owner_bucket_from_fields,
)
from tests.helpers.attribution_contract import (
    ALLOWED_MUTATION_CLASSIFICATIONS,
    ALLOWED_REPAIR_KINDS,
    ATTRIBUTION_ORIGIN_CLASSIFIER_INFERRED,
    ATTRIBUTION_ORIGIN_DIRECT,
    ATTRIBUTION_ORIGIN_PROJECTED,
    REPLACEMENT_PATH_FIRST_MENTION,
    REPLACEMENT_PATH_OPENING_FALLBACK,
    REPLACEMENT_PATH_REFERENTIAL,
    REPLACEMENT_PATH_REPAIR_MUTATION,
    REPLACEMENT_PATH_RESPONSE_TYPE,
    REPLACEMENT_PATH_SANITIZER,
    REPLACEMENT_PATH_SEALED,
    REPLACEMENT_PATH_STRICT_SOCIAL,
    REPLACEMENT_PATH_VISIBILITY,
    REPLACEMENT_PATHS,
    REQUIRED_ATTRIBUTION_FIELDS,
    is_taxonomy_valid,
)
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_classification_sync import (
    exact_value_drift_row,
    observed_sanitizer_empty_fallback_row,
    observed_social_fallback_row,
    observed_visibility_replacement_row,
    response_type_repair_drift_row,
)
from tests.helpers.opening_fallback_evidence import (
    OPENING_FAILED_CLOSED_REPAIR_KIND,
    OPENING_SUCCESS_REPAIR_KIND,
    fail_closed_opening_fem_meta,
    successful_opening_fem_meta,
)

# Re-export contract symbols for existing test imports.
__all__ = [
    "ALLOWED_MUTATION_CLASSIFICATIONS",
    "ALLOWED_REPAIR_KINDS",
    "ATTRIBUTION_ORIGIN_CLASSIFIER_INFERRED",
    "ATTRIBUTION_ORIGIN_DIRECT",
    "ATTRIBUTION_ORIGIN_PROJECTED",
    "REPLACEMENT_PATHS",
    "REQUIRED_ATTRIBUTION_FIELDS",
    "AttributionRecord",
    "baseline_attribution_classifier_inputs",
    "baseline_attribution_fem_fixtures",
    "build_baseline_attribution_corpus",
    "write_bs3_contract_compliance_report",
]

BS1_BASELINE_COMPLETENESS: dict[str, Any] = {
    "total_records": 56,
    "strict_complete_records": 0,
    "resolved_complete_records": 3,
    "strict_completeness_pct": 0.0,
    "resolved_completeness_pct": 5.36,
}

BS1_BASELINE_MISSING_FIELD_TOTALS: dict[str, int] = {
    "repair_kind": 45,
    "owner_bucket": 44,
    "mutation_classification": 16,
    "source_family": 8,
    "recurrence_key": 5,
}

BS5_BASELINE_COMPLETENESS: dict[str, Any] = {
    "total_records": 56,
    "strict_complete_records": 0,
    "resolved_complete_records": 48,
    "strict_completeness_pct": 0.0,
    "resolved_completeness_pct": 85.71,
}

BS5_BASELINE_MISSING_FIELD_TOTALS: dict[str, int] = {
    "repair_kind": 0,
    "owner_bucket": 0,
    "mutation_classification": 8,
    "source_family": 0,
    "recurrence_key": 0,
}


def _repair_kind_from_fem(fem: Mapping[str, Any]) -> str | None:
    for key in (
        "producer_repair_kind",
        "response_type_repair_kind",
        "fallback_behavior_repair_kind",
    ):
        value = _non_empty(fem.get(key))
        if value:
            return value
    return None


def _replay_projection_helpers() -> tuple[Any, Any, Any]:
    from game.final_emission_replay_projection import (
        build_fem_runtime_lineage_events,
        project_sealed_replacement_subkind_from_fem,
        project_source_family_from_fallback_kind,
    )

    return (
        build_fem_runtime_lineage_events,
        project_sealed_replacement_subkind_from_fem,
        project_source_family_from_fallback_kind,
    )


class AttributionRecord(TypedDict):
    owner_bucket: str | None
    source_family: str | None
    repair_kind: str | None
    recurrence_key: str | None
    mutation_classification: str | None
    attribution_origin: dict[str, str]
    replacement_path: str
    inferred_fields: list[str]
    missing_fields: list[str]
    source_kind: NotRequired[str]


def _non_empty(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_taxonomy_valid(field: str, value: str | None) -> bool:
    return is_taxonomy_valid(field, value)


def _finalize_attribution_record(record: AttributionRecord) -> AttributionRecord:
    origins = record.get("attribution_origin") or {}
    inferred_fields: list[str] = []
    missing_fields: list[str] = []
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        value = _non_empty(record.get(field))
        origin = origins.get(field)
        if value is None or not _is_taxonomy_valid(field, value):
            missing_fields.append(field)
            continue
        if origin in {ATTRIBUTION_ORIGIN_PROJECTED, ATTRIBUTION_ORIGIN_CLASSIFIER_INFERRED}:
            inferred_fields.append(field)
    record["inferred_fields"] = sorted(set(inferred_fields))
    record["missing_fields"] = sorted(set(missing_fields))
    return record


def _blank_record(*, replacement_path: str, source_kind: str) -> AttributionRecord:
    return {
        "owner_bucket": None,
        "source_family": None,
        "repair_kind": None,
        "recurrence_key": None,
        "mutation_classification": None,
        "attribution_origin": {},
        "replacement_path": replacement_path,
        "inferred_fields": [],
        "missing_fields": list(REQUIRED_ATTRIBUTION_FIELDS),
        "source_kind": source_kind,
    }


def _set_field(
    record: AttributionRecord,
    field: str,
    value: Any,
    *,
    origin: str,
) -> None:
    normalized = _non_empty(value)
    if normalized is None:
        return
    record[field] = normalized  # type: ignore[literal-required]
    record["attribution_origin"][field] = origin


def detect_replacement_path_from_fem(fem: Mapping[str, Any]) -> str | None:
    """Return the canonical replacement path for applied FEM evidence, if any."""
    if fem.get("visibility_replacement_applied") is True:
        return REPLACEMENT_PATH_VISIBILITY
    if fem.get("first_mention_replacement_applied") is True:
        return REPLACEMENT_PATH_FIRST_MENTION
    if fem.get("referential_clarity_replacement_applied") is True:
        return REPLACEMENT_PATH_REFERENTIAL
    if fem.get("referential_clarity_local_substitution_applied") is True:
        return REPLACEMENT_PATH_REFERENTIAL
    if (
        fem.get("sanitizer_empty_fallback_used") is True
        or fem.get("sanitizer_lineage_empty_fallback_used") is True
        or fem.get("sanitizer_strict_social_fallback_used") is True
        or _non_empty(fem.get("producer_repair_kind")) == "sanitizer_strip_only"
    ):
        return REPLACEMENT_PATH_SANITIZER
    if fem.get("response_type_repair_used") is True:
        return REPLACEMENT_PATH_RESPONSE_TYPE
    if fem.get("passive_scene_concrete_beat_satisfier_applied") is True:
        return REPLACEMENT_PATH_REPAIR_MUTATION
    if fem.get("opening_recovered_via_fallback") is True or fem.get("opening_fallback_failed_closed") is True:
        return REPLACEMENT_PATH_OPENING_FALLBACK
    final_source = _non_empty(fem.get("final_emitted_source")) or ""
    if any(token in final_source.lower() for token in ("strict_social", "deterministic_social", "social_emission_integrity")):
        return REPLACEMENT_PATH_STRICT_SOCIAL
    repair_flags = (
        "answer_completeness_repaired",
        "fallback_behavior_repaired",
        "narrative_authenticity_repaired",
        "tone_escalation_repaired",
        "anti_railroading_repaired",
        "context_separation_repaired",
        "player_facing_narration_purity_repaired",
        "answer_shape_primacy_repaired",
        "narrative_authority_repaired",
        "social_response_structure_repair_applied",
        "response_delta_repaired",
    )
    if any(fem.get(flag) is True for flag in repair_flags):
        return REPLACEMENT_PATH_REPAIR_MUTATION
    _, project_sealed_replacement_subkind_from_fem, _ = _replay_projection_helpers()
    if _non_empty(fem.get("final_route")) == "replaced" or project_sealed_replacement_subkind_from_fem(fem):
        return REPLACEMENT_PATH_SEALED
    return None


def _infer_source_family_from_fem(fem: Mapping[str, Any], replacement_path: str) -> str | None:
    if fem.get("passive_scene_concrete_beat_satisfier_applied") is True:
        return "final_emission_gate"
    if replacement_path == REPLACEMENT_PATH_OPENING_FALLBACK:
        return "opening_fallback"
    if replacement_path == REPLACEMENT_PATH_SANITIZER:
        return "output_sanitizer"
    if replacement_path == REPLACEMENT_PATH_RESPONSE_TYPE:
        return "final_emission_gate"
    if replacement_path in {
        REPLACEMENT_PATH_VISIBILITY,
        REPLACEMENT_PATH_FIRST_MENTION,
        REPLACEMENT_PATH_REFERENTIAL,
        REPLACEMENT_PATH_SEALED,
        REPLACEMENT_PATH_STRICT_SOCIAL,
    }:
        return "final_emission_gate"
    if replacement_path == REPLACEMENT_PATH_REPAIR_MUTATION:
        return "fallback_behavior"
    return None


def _infer_source_family_from_lineage(event: Mapping[str, Any]) -> str | None:
    _, _, project_source_family_from_fallback_kind = _replay_projection_helpers()
    fallback_kind = _non_empty(event.get("fallback_kind")) or ""
    projected = project_source_family_from_fallback_kind(fallback_kind)
    if projected:
        return projected
    if event.get("event_kind") == "gate_outcome":
        stage = _non_empty(event.get("stage")) or ""
        owner = _non_empty(event.get("owner")) or ""
        if stage == "sanitizer" or owner == "game.output_sanitizer":
            return "output_sanitizer"
        if stage == "gate" or owner == "game.final_emission_gate":
            return "final_emission_gate"
    mutation_kind = _non_empty(event.get("mutation_kind")) or ""
    if mutation_kind in {
        "response_type_repair_mutation",
        "fallback_mutation",
        "final_emission_mutation",
        "visibility_replacement_mutation",
        "first_mention_replacement_mutation",
        "referential_clarity_replacement_mutation",
        "sealed_replacement_mutation",
    }:
        return "final_emission_gate"
    if mutation_kind.endswith("_repair_mutation"):
        return "fallback_behavior"
    if mutation_kind in {"sanitizer_mutation"}:
        return "output_sanitizer"
    if mutation_kind == "repair_only_mutation":
        return "fallback_behavior"
    return None


def _owner_bucket_from_fem(fem: Mapping[str, Any], replacement_path: str) -> tuple[str | None, str | None]:
    visibility = _non_empty(fem.get("visibility_fallback_owner_bucket"))
    if visibility:
        return visibility, ATTRIBUTION_ORIGIN_DIRECT
    sealed = _non_empty(fem.get("sealed_fallback_owner_bucket"))
    if sealed:
        return sealed, ATTRIBUTION_ORIGIN_DIRECT
    if replacement_path == REPLACEMENT_PATH_VISIBILITY:
        projected = visibility_fallback_owner_bucket_from_fields(
            fallback_pool=_non_empty(fem.get("visibility_fallback_pool")) or "",
            fallback_kind=_non_empty(fem.get("visibility_fallback_kind")) or "",
            final_emitted_source=_non_empty(fem.get("final_emitted_source")) or "",
        )
        if projected:
            return projected, ATTRIBUTION_ORIGIN_PROJECTED
    if replacement_path == REPLACEMENT_PATH_SEALED:
        projected = sealed_fallback_owner_bucket_from_fields(
            final_emitted_source=_non_empty(fem.get("final_emitted_source")) or "",
            strict_social_route=fem.get("strict_social_active") is True,
        )
        if projected:
            return projected, ATTRIBUTION_ORIGIN_PROJECTED
    if replacement_path == REPLACEMENT_PATH_OPENING_FALLBACK:
        opening_direct = _non_empty(fem.get("opening_fallback_owner_bucket"))
        if opening_direct:
            return opening_direct, ATTRIBUTION_ORIGIN_DIRECT
        projected = opening_fallback_owner_bucket_from_meta(fem)
        if projected:
            return projected, ATTRIBUTION_ORIGIN_PROJECTED
    opening_direct = _non_empty(fem.get("opening_fallback_owner_bucket"))
    if opening_direct:
        return opening_direct, ATTRIBUTION_ORIGIN_DIRECT
    return None, None


def _mutation_classification_from_lineage_events(events: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for event in events:
        if event.get("event_kind") != "mutation":
            continue
        mutation_kind = _non_empty(event.get("mutation_kind"))
        if mutation_kind:
            return mutation_kind, ATTRIBUTION_ORIGIN_PROJECTED
    return None, None


def _recurrence_key_from_lineage_events(events: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    for event in events:
        key = _non_empty(event.get("recurrence_key"))
        if key:
            return key, ATTRIBUTION_ORIGIN_PROJECTED
    return None, None


_PASSIVE_SCENE_CONCRETE_BEAT_MUTATION_KIND: str = "final_emission_mutation"
_PASSIVE_SCENE_CONCRETE_BEAT_GATE_OWNER: str = "game.final_emission_gate"
_PASSIVE_SCENE_CONCRETE_BEAT_OWNER_BUCKET: str = "sealed-gate"
_REPAIR_MUTATION_GATE_OWNER_BUCKET: str = "sealed-gate"
_SANITIZER_PRODUCER_REPAIR_KINDS: frozenset[str] = frozenset(
    {
        "sanitizer_empty_output",
        "sanitizer_strip_only",
    }
)


def _projected_passive_scene_concrete_beat_attribution(
    fem: Mapping[str, Any],
) -> dict[str, tuple[str, str]] | None:
    """Project passive-scene upstream satisfier attribution from contract FEM evidence."""
    if fem.get("passive_scene_concrete_beat_satisfier_applied") is not True:
        return None
    repair_kind = _non_empty(fem.get("producer_repair_kind"))
    if repair_kind != "passive_scene_concrete_beat":
        return None
    from game.runtime_lineage_telemetry import build_recurrence_key

    recurrence_key = build_recurrence_key(
        event_kind="mutation",
        stage="gate",
        owner=_PASSIVE_SCENE_CONCRETE_BEAT_GATE_OWNER,
        repair_kind=repair_kind,
        mutation_kind=_PASSIVE_SCENE_CONCRETE_BEAT_MUTATION_KIND,
    )
    return {
        "owner_bucket": (_PASSIVE_SCENE_CONCRETE_BEAT_OWNER_BUCKET, ATTRIBUTION_ORIGIN_PROJECTED),
        "recurrence_key": (recurrence_key, ATTRIBUTION_ORIGIN_PROJECTED),
        "mutation_classification": (
            _PASSIVE_SCENE_CONCRETE_BEAT_MUTATION_KIND,
            ATTRIBUTION_ORIGIN_PROJECTED,
        ),
    }


def _sanitizer_producer_attribution_evidence(fem: Mapping[str, Any]) -> bool:
    if fem.get("sanitizer_empty_fallback_used") is True or fem.get("sanitizer_lineage_empty_fallback_used") is True:
        return True
    for key in ("sanitizer_lineage_changed_count", "sanitizer_changed_count"):
        changed = fem.get(key)
        if isinstance(changed, (int, float)) and not isinstance(changed, bool) and changed > 0:
            return True
    return _non_empty(fem.get("producer_repair_kind")) in _SANITIZER_PRODUCER_REPAIR_KINDS


def _projected_sanitizer_owner_bucket_from_fem(
    fem: Mapping[str, Any],
) -> tuple[str, str] | None:
    """Project sanitizer owner buckets from producer-stamped FEM or co-stamp semantics."""
    direct = _non_empty(fem.get("sealed_fallback_owner_bucket"))
    if direct:
        return direct, ATTRIBUTION_ORIGIN_DIRECT
    repair_kind = _non_empty(fem.get("producer_repair_kind"))
    if repair_kind in _SANITIZER_PRODUCER_REPAIR_KINDS and _sanitizer_producer_attribution_evidence(fem):
        from game.final_emission_ownership_schema import SEALED_FALLBACK_OWNER_UNKNOWN_NONE

        return SEALED_FALLBACK_OWNER_UNKNOWN_NONE, ATTRIBUTION_ORIGIN_PROJECTED
    return None


def _projected_gate_family_owner_bucket_from_fem(
    fem: Mapping[str, Any],
    *,
    replacement_path: str,
) -> tuple[str, str] | None:
    """Project gate-family owner buckets from stamped or inferable FEM evidence."""
    owner_bucket, owner_origin = _owner_bucket_from_fem(fem, replacement_path)
    if owner_bucket and owner_origin:
        return owner_bucket, owner_origin
    if replacement_path == REPLACEMENT_PATH_STRICT_SOCIAL:
        repair_kind = _non_empty(fem.get("producer_repair_kind"))
        if fem.get("strict_social_active") is True and repair_kind == "strict_social_repair":
            from game.final_emission_ownership_schema import SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED

            return SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED, ATTRIBUTION_ORIGIN_PROJECTED
    return None


def _projected_gate_family_repair_kind_from_fem(
    fem: Mapping[str, Any],
    *,
    replacement_path: str,
) -> tuple[str, str] | None:
    """Project repair kinds already stamped on FEM for gate-family replacement paths."""
    if replacement_path == REPLACEMENT_PATH_VISIBILITY:
        repair_kind = _non_empty(fem.get("producer_repair_kind"))
        if repair_kind and fem.get("visibility_replacement_applied") is True:
            return repair_kind, ATTRIBUTION_ORIGIN_PROJECTED
    if replacement_path == REPLACEMENT_PATH_FIRST_MENTION:
        repair_kind = _non_empty(fem.get("producer_repair_kind"))
        if repair_kind and fem.get("first_mention_replacement_applied") is True:
            return repair_kind, ATTRIBUTION_ORIGIN_PROJECTED
    if replacement_path == REPLACEMENT_PATH_REFERENTIAL:
        repair_kind = _non_empty(fem.get("producer_repair_kind"))
        if repair_kind and (
            fem.get("referential_clarity_replacement_applied") is True
            or fem.get("referential_clarity_local_substitution_applied") is True
        ):
            return repair_kind, ATTRIBUTION_ORIGIN_PROJECTED
    if replacement_path == REPLACEMENT_PATH_STRICT_SOCIAL:
        repair_kind = _non_empty(fem.get("producer_repair_kind"))
        if repair_kind and (
            fem.get("strict_social_active") is True or fem.get("response_type_repair_used") is True
        ):
            return repair_kind, ATTRIBUTION_ORIGIN_PROJECTED
    if replacement_path == REPLACEMENT_PATH_RESPONSE_TYPE:
        if fem.get("response_type_repair_used") is True:
            repair_kind = _non_empty(fem.get("response_type_repair_kind"))
            if repair_kind:
                return repair_kind, ATTRIBUTION_ORIGIN_PROJECTED
    if replacement_path == REPLACEMENT_PATH_OPENING_FALLBACK:
        repair_kind = _repair_kind_from_fem(fem)
        if repair_kind:
            return repair_kind, ATTRIBUTION_ORIGIN_PROJECTED
    if replacement_path == REPLACEMENT_PATH_SEALED:
        repair_kind = _repair_kind_from_fem(fem)
        if repair_kind:
            return repair_kind, ATTRIBUTION_ORIGIN_PROJECTED
    return None


def _projected_repair_mutation_owner_bucket(
    fem: Mapping[str, Any],
    *,
    replacement_path: str,
) -> tuple[str, str] | None:
    """Project gate-family owner buckets for repair-mutation producer stamps."""
    if replacement_path != REPLACEMENT_PATH_REPAIR_MUTATION:
        return None
    passive_scene = _projected_passive_scene_concrete_beat_attribution(fem)
    if passive_scene is not None:
        return passive_scene["owner_bucket"]
    if fem.get("fallback_behavior_repaired") is True:
        direct = _non_empty(fem.get("sealed_fallback_owner_bucket"))
        if direct:
            return direct, ATTRIBUTION_ORIGIN_DIRECT
        return _REPAIR_MUTATION_GATE_OWNER_BUCKET, ATTRIBUTION_ORIGIN_PROJECTED
    return None


def _apply_projected_fem_attribution(
    record: AttributionRecord,
    fem: Mapping[str, Any],
    *,
    replacement_path: str,
) -> None:
    """Fill read-side attribution gaps from producer-stamped FEM evidence."""
    if record.get("owner_bucket") is None:
        projected_owner = _projected_repair_mutation_owner_bucket(fem, replacement_path=replacement_path)
        if projected_owner is None and replacement_path == REPLACEMENT_PATH_SANITIZER:
            projected_owner = _projected_sanitizer_owner_bucket_from_fem(fem)
        if projected_owner is None and replacement_path in {
            REPLACEMENT_PATH_VISIBILITY,
            REPLACEMENT_PATH_FIRST_MENTION,
            REPLACEMENT_PATH_REFERENTIAL,
            REPLACEMENT_PATH_SEALED,
            REPLACEMENT_PATH_STRICT_SOCIAL,
            REPLACEMENT_PATH_RESPONSE_TYPE,
        }:
            projected_owner = _projected_gate_family_owner_bucket_from_fem(
                fem,
                replacement_path=replacement_path,
            )
        if projected_owner is not None:
            _set_field(record, "owner_bucket", projected_owner[0], origin=projected_owner[1])

    passive_scene = _projected_passive_scene_concrete_beat_attribution(fem)
    if passive_scene is None:
        return
    if record.get("recurrence_key") is None:
        recurrence_key, recurrence_origin = passive_scene["recurrence_key"]
        _set_field(record, "recurrence_key", recurrence_key, origin=recurrence_origin)
    if record.get("mutation_classification") is None:
        mutation_kind, mutation_origin = passive_scene["mutation_classification"]
        _set_field(record, "mutation_classification", mutation_kind, origin=mutation_origin)


def _lineage_mutation_attribution_from_fem(
    event: Mapping[str, Any],
    fem: Mapping[str, Any],
    *,
    replacement_path: str | None = None,
) -> dict[str, tuple[str, str]]:
    """Project producer repair attribution onto lineage events when replay omits it."""
    event_kind = event.get("event_kind")
    if event_kind not in {"mutation", "fallback_selected", "gate_outcome"}:
        return {}

    producer_repair_kind = _non_empty(fem.get("producer_repair_kind"))
    mutation_kind = _non_empty(event.get("mutation_kind"))
    fallback_kind = _non_empty(event.get("fallback_kind"))
    stage = _non_empty(event.get("stage"))
    projected: dict[str, tuple[str, str]] = {}

    if producer_repair_kind and not _non_empty(event.get("repair_kind")):
        if mutation_kind == "sanitizer_mutation" and producer_repair_kind in _SANITIZER_PRODUCER_REPAIR_KINDS:
            projected["repair_kind"] = (producer_repair_kind, ATTRIBUTION_ORIGIN_PROJECTED)
        elif (
            mutation_kind == "fallback_behavior_repair_mutation"
            and producer_repair_kind == "fallback_behavior_repair"
        ):
            projected["repair_kind"] = (producer_repair_kind, ATTRIBUTION_ORIGIN_PROJECTED)
        elif (
            event_kind == "gate_outcome"
            and stage == "sanitizer"
            and producer_repair_kind in _SANITIZER_PRODUCER_REPAIR_KINDS
        ):
            projected["repair_kind"] = (producer_repair_kind, ATTRIBUTION_ORIGIN_PROJECTED)

    if replacement_path and not _non_empty(event.get("repair_kind")) and "repair_kind" not in projected:
        gate_repair = _projected_gate_family_repair_kind_from_fem(fem, replacement_path=replacement_path)
        if gate_repair is not None:
            projected["repair_kind"] = gate_repair

    if not _non_empty(event.get("fallback_owner_bucket")):
        sanitizer_owner = _projected_sanitizer_owner_bucket_from_fem(fem)
        if sanitizer_owner is not None:
            if mutation_kind == "sanitizer_mutation":
                projected["owner_bucket"] = (
                    sanitizer_owner[0],
                    ATTRIBUTION_ORIGIN_PROJECTED,
                )
            elif fallback_kind == "sanitizer_empty_output" or str(fallback_kind or "").startswith("sanitizer"):
                projected["owner_bucket"] = (
                    sanitizer_owner[0],
                    ATTRIBUTION_ORIGIN_PROJECTED,
                )
            elif event_kind == "gate_outcome" and stage == "sanitizer":
                projected["owner_bucket"] = (
                    sanitizer_owner[0],
                    ATTRIBUTION_ORIGIN_PROJECTED,
                )
        if replacement_path == REPLACEMENT_PATH_REPAIR_MUTATION and "owner_bucket" not in projected:
            repair_mutation_owner = _projected_repair_mutation_owner_bucket(
                fem,
                replacement_path=replacement_path,
            )
            if repair_mutation_owner is not None:
                projected["owner_bucket"] = repair_mutation_owner
        if replacement_path and "owner_bucket" not in projected:
            gate_owner = _projected_gate_family_owner_bucket_from_fem(
                fem,
                replacement_path=replacement_path,
            )
            if gate_owner is not None:
                projected["owner_bucket"] = gate_owner

    return projected


def attribution_record_from_fem(
    fem: Mapping[str, Any],
    *,
    replacement_path: str | None = None,
) -> AttributionRecord | None:
    """Construct a canonical attribution record from finalized FEM metadata."""
    path = replacement_path or detect_replacement_path_from_fem(fem)
    if path is None:
        return None
    record = _blank_record(replacement_path=path, source_kind="fem_metadata")
    owner_bucket, owner_origin = _owner_bucket_from_fem(fem, path)
    if owner_bucket and owner_origin:
        _set_field(record, "owner_bucket", owner_bucket, origin=owner_origin)

    repair_kind = _repair_kind_from_fem(fem)
    if repair_kind:
        _set_field(record, "repair_kind", repair_kind, origin=ATTRIBUTION_ORIGIN_DIRECT)

    source_family = _infer_source_family_from_fem(fem, path)
    if source_family:
        _set_field(record, "source_family", source_family, origin=ATTRIBUTION_ORIGIN_PROJECTED)

    build_fem_runtime_lineage_events, _, _ = _replay_projection_helpers()
    lineage_events = build_fem_runtime_lineage_events(fem)
    recurrence_key, recurrence_origin = _recurrence_key_from_lineage_events(lineage_events)
    if recurrence_key and recurrence_origin:
        _set_field(record, "recurrence_key", recurrence_key, origin=recurrence_origin)

    mutation_kind, mutation_origin = _mutation_classification_from_lineage_events(lineage_events)
    if mutation_kind and mutation_origin:
        _set_field(record, "mutation_classification", mutation_kind, origin=mutation_origin)

    _apply_projected_fem_attribution(record, fem, replacement_path=path)

    return _finalize_attribution_record(record)


def detect_replacement_path_from_lineage_event(event: Mapping[str, Any]) -> str | None:
    fallback_kind = _non_empty(event.get("fallback_kind")) or ""
    if fallback_kind in {"visibility_hard_replacement", "visibility_or_scene_replacement"}:
        return REPLACEMENT_PATH_VISIBILITY
    if fallback_kind == "first_mention_hard_replacement":
        return REPLACEMENT_PATH_FIRST_MENTION
    if fallback_kind == "referential_clarity_hard_replacement":
        return REPLACEMENT_PATH_REFERENTIAL
    if fallback_kind.startswith("sanitizer"):
        return REPLACEMENT_PATH_SANITIZER
    if fallback_kind in {"scene_opening", "opening_failed_closed"}:
        return REPLACEMENT_PATH_OPENING_FALLBACK
    if fallback_kind == "response_type_prepared_emission":
        return REPLACEMENT_PATH_RESPONSE_TYPE
    if fallback_kind == "strict_social_fallback":
        return REPLACEMENT_PATH_STRICT_SOCIAL
    if fallback_kind.startswith("sealed_"):
        return REPLACEMENT_PATH_SEALED
    mutation_kind = _non_empty(event.get("mutation_kind")) or ""
    if mutation_kind == "repair_only_mutation" or mutation_kind.endswith("_repair_mutation"):
        return REPLACEMENT_PATH_REPAIR_MUTATION
    if mutation_kind == "response_type_repair_mutation":
        return REPLACEMENT_PATH_RESPONSE_TYPE
    if event.get("event_kind") == "fallback_selected":
        return REPLACEMENT_PATH_SEALED
    return None


def attribution_record_from_lineage_event(
    event: Mapping[str, Any],
    *,
    replacement_path: str | None = None,
    fem: Mapping[str, Any] | None = None,
) -> AttributionRecord | None:
    """Construct a canonical attribution record from one runtime lineage event."""
    path = replacement_path or detect_replacement_path_from_lineage_event(event)
    if path is None:
        return None
    record = _blank_record(replacement_path=path, source_kind="runtime_lineage_event")

    projected_fields = (
        _lineage_mutation_attribution_from_fem(event, fem, replacement_path=path)
        if isinstance(fem, Mapping)
        else {}
    )

    owner_bucket = _non_empty(event.get("fallback_owner_bucket")) or (
        projected_fields.get("owner_bucket", (None, None))[0]
    )
    if owner_bucket:
        owner_origin = (
            ATTRIBUTION_ORIGIN_DIRECT
            if _non_empty(event.get("fallback_owner_bucket"))
            else projected_fields["owner_bucket"][1]
        )
        _set_field(record, "owner_bucket", owner_bucket, origin=owner_origin)

    repair_kind = _non_empty(event.get("repair_kind")) or projected_fields.get("repair_kind", (None, None))[0]
    if repair_kind:
        repair_origin = (
            ATTRIBUTION_ORIGIN_DIRECT
            if _non_empty(event.get("repair_kind"))
            else projected_fields["repair_kind"][1]
        )
        _set_field(record, "repair_kind", repair_kind, origin=repair_origin)

    recurrence_key = _non_empty(event.get("recurrence_key"))
    if recurrence_key:
        _set_field(record, "recurrence_key", recurrence_key, origin=ATTRIBUTION_ORIGIN_DIRECT)

    mutation_kind = _non_empty(event.get("mutation_kind"))
    if not mutation_kind:
        fallback_kind = _non_empty(event.get("fallback_kind"))
        if fallback_kind:
            from game.final_emission_replay_projection import project_mutation_classification_from_fallback_kind

            mutation_kind = project_mutation_classification_from_fallback_kind(fallback_kind)
            if mutation_kind:
                _set_field(record, "mutation_classification", mutation_kind, origin=ATTRIBUTION_ORIGIN_PROJECTED)
    elif mutation_kind:
        _set_field(record, "mutation_classification", mutation_kind, origin=ATTRIBUTION_ORIGIN_DIRECT)

    source_family = _infer_source_family_from_lineage(event)
    if source_family:
        _set_field(record, "source_family", source_family, origin=ATTRIBUTION_ORIGIN_PROJECTED)

    return _finalize_attribution_record(record)


def attribution_record_from_replay_projection(
    observed_turn: Mapping[str, Any],
    *,
    replacement_path: str | None = None,
) -> AttributionRecord | None:
    """Construct a canonical attribution record from a golden replay observed turn."""
    fem = observed_turn if isinstance(observed_turn, Mapping) else {}
    path = replacement_path or detect_replacement_path_from_fem(fem)
    if path is None:
        return None
    record = _blank_record(replacement_path=path, source_kind="replay_projection")

    for bucket_field in (
        "visibility_fallback_owner_bucket",
        "sealed_fallback_owner_bucket",
        "opening_fallback_owner_bucket",
    ):
        bucket = _non_empty(fem.get(bucket_field))
        if bucket:
            _set_field(record, "owner_bucket", bucket, origin=ATTRIBUTION_ORIGIN_DIRECT)
            break
    if record["owner_bucket"] is None:
        owner_bucket, owner_origin = _owner_bucket_from_fem(fem, path)
        if owner_bucket and owner_origin:
            _set_field(record, "owner_bucket", owner_bucket, origin=owner_origin)

    repair_kind = _repair_kind_from_fem(fem)
    if repair_kind:
        _set_field(record, "repair_kind", repair_kind, origin=ATTRIBUTION_ORIGIN_DIRECT)

    source_family = _infer_source_family_from_fem(fem, path)
    if source_family:
        _set_field(record, "source_family", source_family, origin=ATTRIBUTION_ORIGIN_PROJECTED)

    raw_events = fem.get("fem_runtime_lineage_events") or fem.get("runtime_lineage_events")
    if isinstance(raw_events, list) and raw_events:
        lineage_events = [event for event in raw_events if isinstance(event, Mapping)]
    else:
        build_fem_runtime_lineage_events, _, _ = _replay_projection_helpers()
        lineage_events = build_fem_runtime_lineage_events(fem)

    recurrence_key, recurrence_origin = _recurrence_key_from_lineage_events(lineage_events)
    if recurrence_key and recurrence_origin:
        _set_field(record, "recurrence_key", recurrence_key, origin=recurrence_origin)

    mutation_kind, mutation_origin = _mutation_classification_from_lineage_events(lineage_events)
    if mutation_kind and mutation_origin:
        _set_field(record, "mutation_classification", mutation_kind, origin=mutation_origin)

    _apply_projected_fem_attribution(record, fem, replacement_path=path)

    return _finalize_attribution_record(record)


def attribution_record_from_failure_classification(
    classification: Mapping[str, Any],
    *,
    replacement_path: str | None = None,
    observed_turn: Mapping[str, Any] | None = None,
) -> AttributionRecord | None:
    """Construct a canonical attribution record from one failure classification row."""
    path = replacement_path
    if path is None:
        field_path = _non_empty(classification.get("field_path")) or ""
        if "visibility" in field_path:
            path = REPLACEMENT_PATH_VISIBILITY
        elif "opening" in field_path:
            path = REPLACEMENT_PATH_OPENING_FALLBACK
        elif classification.get("sanitizer_empty_fallback_used") is True:
            path = REPLACEMENT_PATH_SANITIZER
        elif classification.get("response_type_repair_used") is True:
            path = REPLACEMENT_PATH_RESPONSE_TYPE
        elif classification.get("sealed_fallback_owner_bucket"):
            path = REPLACEMENT_PATH_SEALED
        elif classification.get("category") == "semantic_mutation":
            path = REPLACEMENT_PATH_REPAIR_MUTATION
        else:
            path = REPLACEMENT_PATH_OPENING_FALLBACK

    record = _blank_record(replacement_path=path, source_kind="failure_classification")

    for bucket_field in (
        "visibility_fallback_owner_bucket",
        "sealed_fallback_owner_bucket",
        "opening_fallback_owner_bucket",
    ):
        bucket = _non_empty(classification.get(bucket_field))
        if bucket:
            origin = (
                ATTRIBUTION_ORIGIN_DIRECT
                if bucket_field.replace("_owner_bucket", "") in str(classification.get("field_path") or "")
                or classification.get(bucket_field) is not None
                else ATTRIBUTION_ORIGIN_CLASSIFIER_INFERRED
            )
            if bucket_field == "opening_fallback_owner_bucket" and classification.get(bucket_field):
                origin = ATTRIBUTION_ORIGIN_CLASSIFIER_INFERRED
            _set_field(record, "owner_bucket", bucket, origin=origin)

    source_family = _non_empty(classification.get("source_family"))
    if source_family:
        _set_field(record, "source_family", source_family, origin=ATTRIBUTION_ORIGIN_DIRECT)

    repair_kind = _non_empty(classification.get("repair_kind"))
    if repair_kind:
        origin = (
            ATTRIBUTION_ORIGIN_DIRECT
            if _non_empty(classification.get("response_type_repair_kind")) == repair_kind
            else ATTRIBUTION_ORIGIN_CLASSIFIER_INFERRED
        )
        _set_field(record, "repair_kind", repair_kind, origin=origin)

    mutation_source = _non_empty(classification.get("mutation_source")) or _non_empty(
        classification.get("emission_sublayer")
    )
    if mutation_source:
        _set_field(
            record,
            "mutation_classification",
            mutation_source,
            origin=ATTRIBUTION_ORIGIN_CLASSIFIER_INFERRED,
        )

    if observed_turn is not None:
        for bucket_field in (
            "visibility_fallback_owner_bucket",
            "sealed_fallback_owner_bucket",
            "opening_fallback_owner_bucket",
        ):
            if record.get("owner_bucket"):
                break
            bucket = _non_empty(observed_turn.get(bucket_field))
            if bucket:
                _set_field(record, "owner_bucket", bucket, origin=ATTRIBUTION_ORIGIN_DIRECT)
        if record.get("recurrence_key") is None:
            raw_events = observed_turn.get("fem_runtime_lineage_events") or observed_turn.get("runtime_lineage_events")
            if isinstance(raw_events, list):
                recurrence_key, recurrence_origin = _recurrence_key_from_lineage_events(
                    [event for event in raw_events if isinstance(event, Mapping)]
                )
                if recurrence_key and recurrence_origin:
                    _set_field(record, "recurrence_key", recurrence_key, origin=recurrence_origin)
        if record.get("source_family") is None:
            fallback_event = None
            raw_events = observed_turn.get("fem_runtime_lineage_events") or observed_turn.get("runtime_lineage_events")
            if isinstance(raw_events, list):
                for event in raw_events:
                    if isinstance(event, Mapping) and event.get("event_kind") == "fallback_selected":
                        fallback_event = event
                        break
            if fallback_event is not None:
                source_family = _infer_source_family_from_lineage(fallback_event)
                if source_family:
                    _set_field(record, "source_family", source_family, origin=ATTRIBUTION_ORIGIN_PROJECTED)
        _apply_projected_fem_attribution(record, observed_turn, replacement_path=path)

    return _finalize_attribution_record(record)


def _is_strict_complete(record: AttributionRecord) -> bool:
    origins = record.get("attribution_origin") or {}
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        value = _non_empty(record.get(field))
        if value is None or not _is_taxonomy_valid(field, value):
            return False
        if origins.get(field) != ATTRIBUTION_ORIGIN_DIRECT:
            return False
    return True


def _is_resolved_complete(record: AttributionRecord) -> bool:
    return not record.get("missing_fields")


def calculate_attribution_completeness(records: Sequence[AttributionRecord]) -> dict[str, Any]:
    """Return strict and resolved completeness metrics for attribution records."""
    total = len(records)
    strict_complete = sum(1 for record in records if _is_strict_complete(record))
    resolved_complete = sum(1 for record in records if _is_resolved_complete(record))
    strict_pct = round(100.0 * strict_complete / total, 2) if total else 0.0
    resolved_pct = round(100.0 * resolved_complete / total, 2) if total else 0.0
    return {
        "total_records": total,
        "complete_records": resolved_complete,
        "strict_complete_records": strict_complete,
        "resolved_complete_records": resolved_complete,
        "strict_completeness_pct": strict_pct,
        "resolved_completeness_pct": resolved_pct,
    }


def build_replacement_path_attribution_report(
    records: Sequence[AttributionRecord],
) -> dict[str, dict[str, Any]]:
    """Return per-path attribution breakdown with missing-field counts."""
    report: dict[str, dict[str, Any]] = {}
    for path in REPLACEMENT_PATHS:
        path_records = [record for record in records if record.get("replacement_path") == path]
        missing_counts = {field: 0 for field in REQUIRED_ATTRIBUTION_FIELDS}
        for record in path_records:
            for field in record.get("missing_fields") or []:
                missing_counts[field] = missing_counts.get(field, 0) + 1
        report[path] = {
            "total": len(path_records),
            "complete": sum(1 for record in path_records if _is_resolved_complete(record)),
            "missing_owner_bucket": missing_counts["owner_bucket"],
            "missing_source_family": missing_counts["source_family"],
            "missing_repair_kind": missing_counts["repair_kind"],
            "missing_recurrence_key": missing_counts["recurrence_key"],
            "missing_mutation_classification": missing_counts["mutation_classification"],
        }
    return report


def _top_missing_fields(records: Sequence[AttributionRecord]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {field: 0 for field in REQUIRED_ATTRIBUTION_FIELDS}
    for record in records:
        for field in record.get("missing_fields") or []:
            counts[field] = counts.get(field, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [(field, count) for field, count in ranked if count > 0]


def _worst_coverage_paths(path_report: Mapping[str, Mapping[str, Any]]) -> list[tuple[str, float]]:
    ranked: list[tuple[str, float]] = []
    for path, stats in path_report.items():
        total = int(stats.get("total") or 0)
        if total == 0:
            continue
        complete = int(stats.get("complete") or 0)
        ranked.append((path, round(100.0 * complete / total, 2)))
    ranked.sort(key=lambda item: (item[1], item[0]))
    return ranked


def render_baseline_attribution_report_md(
    *,
    completeness: Mapping[str, Any],
    path_report: Mapping[str, Mapping[str, Any]],
    records: Sequence[AttributionRecord],
) -> str:
    """Render the BS1 baseline attribution markdown report."""
    top_missing = _top_missing_fields(records)
    worst_paths = _worst_coverage_paths(path_report)
    lines = [
        "# BS Attribution Baseline Report",
        "",
        "> Read-side inventory baseline generated by BS1 canonical attribution tooling.",
        "",
        "## Summary",
        "",
        f"- Strict completeness: **{completeness['strict_completeness_pct']}%** "
        f"({completeness['strict_complete_records']}/{completeness['total_records']})",
        f"- Resolved completeness: **{completeness['resolved_completeness_pct']}%** "
        f"({completeness['resolved_complete_records']}/{completeness['total_records']})",
        "",
        "## Per-Path Completeness",
        "",
        "| Replacement path | Total | Complete | Missing owner | Missing source | Missing repair | Missing recurrence | Missing mutation |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for path in REPLACEMENT_PATHS:
        stats = path_report.get(path) or {}
        lines.append(
            "| {path} | {total} | {complete} | {owner} | {source} | {repair} | {recurrence} | {mutation} |".format(
                path=path,
                total=stats.get("total", 0),
                complete=stats.get("complete", 0),
                owner=stats.get("missing_owner_bucket", 0),
                source=stats.get("missing_source_family", 0),
                repair=stats.get("missing_repair_kind", 0),
                recurrence=stats.get("missing_recurrence_key", 0),
                mutation=stats.get("missing_mutation_classification", 0),
            )
        )
    lines.extend(["", "## Top Missing Fields", ""])
    if top_missing:
        for field, count in top_missing:
            lines.append(f"- `{field}`: {count} record(s)")
    else:
        lines.append("- _none_")
    lines.extend(["", "## Paths With Worst Attribution Coverage", ""])
    if worst_paths:
        for path, pct in worst_paths[:5]:
            lines.append(f"- {path}: {pct}% resolved complete")
    else:
        lines.append("- _none_")
    lines.append("")
    return "\n".join(lines)


def baseline_attribution_fem_fixtures() -> list[dict[str, Any]]:
    """Return FEM payloads used by the deterministic baseline attribution corpus."""
    return [fem for _path, fem, _drift in _baseline_corpus_fixtures()]


def baseline_attribution_classifier_inputs() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Return (observed_turn, drift_row) pairs for baseline classifier audit inputs."""
    build_fem_runtime_lineage_events, _, _ = _replay_projection_helpers()
    inputs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for path, fem, drift_row in _baseline_corpus_fixtures():
        if drift_row is None:
            continue
        observed = dict(fem)
        if path == REPLACEMENT_PATH_VISIBILITY:
            observed.update(observed_visibility_replacement_row())
        elif path == REPLACEMENT_PATH_SANITIZER and fem.get("sanitizer_empty_fallback_used") is True:
            observed.update(observed_sanitizer_empty_fallback_row())
        elif path == REPLACEMENT_PATH_STRICT_SOCIAL:
            observed.update(observed_social_fallback_row())
        observed["fem_runtime_lineage_events"] = build_fem_runtime_lineage_events(fem)
        inputs.append((observed, drift_row))
    return inputs


def _baseline_corpus_fixtures() -> list[tuple[str, dict[str, Any], dict[str, Any] | None]]:
    """Deterministic FEM fixtures for baseline attribution corpus construction."""
    return [
        (
            REPLACEMENT_PATH_VISIBILITY,
            {
                "final_route": "replaced",
                "final_emitted_source": "global_scene_fallback",
                "visibility_replacement_applied": True,
                "visibility_fallback_owner_bucket": "sealed-gate",
                "visibility_fallback_pool": "global_scene_narrative",
                "visibility_fallback_kind": "narrative_safe_fallback",
                "producer_repair_kind": "visibility_enforcement",
            },
            None,
        ),
        (
            REPLACEMENT_PATH_FIRST_MENTION,
            {
                "final_route": "replaced",
                "final_emitted_source": "global_scene_fallback",
                "first_mention_replacement_applied": True,
                "visibility_fallback_pool": "global_scene_narrative",
                "visibility_fallback_kind": "narrative_safe_fallback",
                "visibility_fallback_owner_bucket": "sealed-gate",
                "sealed_fallback_owner_bucket": "sealed-gate",
                "producer_repair_kind": "first_mention_enforcement",
            },
            None,
        ),
        (
            REPLACEMENT_PATH_REFERENTIAL,
            {
                "final_route": "replaced",
                "final_emitted_source": "global_scene_fallback",
                "referential_clarity_replacement_applied": True,
                "visibility_fallback_pool": "global_scene_narrative",
                "visibility_fallback_kind": "narrative_safe_fallback",
                "visibility_fallback_owner_bucket": "sealed-gate",
                "sealed_fallback_owner_bucket": "sealed-gate",
                "producer_repair_kind": "referential_clarity_enforcement",
            },
            None,
        ),
        (
            REPLACEMENT_PATH_REPAIR_MUTATION,
            {
                "final_route": "accept_candidate",
                "passive_scene_concrete_beat_satisfier_applied": True,
                "passive_scene_pressure_fallback_avoided": True,
                "passive_scene_concrete_beat_type": "guard_reaction",
                "producer_repair_kind": "passive_scene_concrete_beat",
                "final_emission_mutation_lineage": ["passive_scene_concrete_beat"],
            },
            exact_value_drift_row(
                "passive_scene_concrete_beat_satisfier_applied",
                expected=False,
                actual=True,
                reason="passive scene upstream satisfier producer stamp",
            ),
        ),
        (
            REPLACEMENT_PATH_SEALED,
            {
                "final_route": "replaced",
                "final_emitted_source": "passive_scene_pressure_fallback",
                "sealed_fallback_owner_bucket": "sealed-gate",
                "fallback_kind": "passive_scene_pressure_fallback",
                "producer_repair_kind": "passive_scene_pressure_fallback",
            },
            None,
        ),
        (
            REPLACEMENT_PATH_RESPONSE_TYPE,
            {
                "final_route": "accept_candidate",
                "response_type_repair_used": True,
                "response_type_repair_kind": "answer_upstream_prepared_repair",
                "upstream_prepared_emission_used": True,
                "sealed_fallback_owner_bucket": "sealed-gate",
            },
            response_type_repair_drift_row(),
        ),
        (
            REPLACEMENT_PATH_SANITIZER,
            {
                "sanitizer_empty_fallback_used": True,
                "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                "final_route": "replaced",
                "final_emitted_source": "global_scene_fallback",
                "sealed_fallback_owner_bucket": "unknown-none",
                "producer_repair_kind": "sanitizer_empty_output",
            },
            exact_value_drift_row(
                "sanitizer_empty_fallback_used",
                expected=False,
                actual=True,
            ),
        ),
        (
            REPLACEMENT_PATH_SANITIZER,
            {
                "sanitizer_empty_fallback_used": False,
                "sanitizer_mode": "strip_only",
                "sanitizer_lineage_mode": "strip_only",
                "sanitizer_event_count": 1,
                "sanitizer_changed_count": 1,
                "sanitizer_lineage_changed_count": 1,
                "final_route": "accept_candidate",
                "final_emitted_source": "generated_candidate",
                "sealed_fallback_owner_bucket": "unknown-none",
                "producer_repair_kind": "sanitizer_strip_only",
            },
            exact_value_drift_row(
                "producer_repair_kind",
                expected=None,
                actual="sanitizer_strip_only",
                reason="sanitizer strip-only producer stamp",
            ),
        ),
        (
            REPLACEMENT_PATH_REPAIR_MUTATION,
            {
                "final_route": "accept_candidate",
                "fallback_behavior_repaired": True,
                "fallback_behavior_repair_kind": "fallback_behavior_repair",
                "producer_repair_kind": "fallback_behavior_repair",
                "sealed_fallback_owner_bucket": "sealed-gate",
                "final_emission_mutation_lineage": ["fallback_behavior_repair"],
            },
            exact_value_drift_row(
                "fallback_behavior_repaired",
                expected=False,
                actual=True,
            ),
        ),
        (
            REPLACEMENT_PATH_OPENING_FALLBACK,
            {
                **successful_opening_fem_meta(
                    final_route="replaced",
                    response_type_repair_kind=OPENING_SUCCESS_REPAIR_KIND,
                ),
                "opening_fallback_owner_bucket": "upstream-prepared",
            },
            exact_value_drift_row(
                "opening_recovered_via_fallback",
                expected=False,
                actual=True,
            ),
        ),
        (
            REPLACEMENT_PATH_STRICT_SOCIAL,
            {
                "final_route": "replaced",
                "strict_social_active": True,
                "final_emitted_source": "strict_social_replacement",
                "response_type_repair_used": True,
                "response_type_repair_kind": "strict_social_dialogue_repair",
                "sealed_fallback_owner_bucket": "strict-social-sealed",
                "producer_repair_kind": "strict_social_repair",
            },
            exact_value_drift_row(
                "final_emitted_source",
                expected="candidate_source",
                actual="strict_social_replacement",
            ),
        ),
    ]


def build_baseline_attribution_corpus() -> list[AttributionRecord]:
    """Return deterministic synthetic baseline records across replacement paths."""
    corpus_fixtures = _baseline_corpus_fixtures()
    records: list[AttributionRecord] = []
    build_fem_runtime_lineage_events, _, _ = _replay_projection_helpers()
    for path, fem, drift_row in corpus_fixtures:
        fem_record = attribution_record_from_fem(fem, replacement_path=path)
        if fem_record is not None:
            records.append(fem_record)

        for event in build_fem_runtime_lineage_events(fem):
            lineage_record = attribution_record_from_lineage_event(
                event,
                replacement_path=path,
                fem=fem,
            )
            if lineage_record is not None:
                records.append(lineage_record)

        observed = dict(fem)
        if path == REPLACEMENT_PATH_VISIBILITY:
            observed.update(observed_visibility_replacement_row())
        elif path == REPLACEMENT_PATH_SANITIZER and fem.get("sanitizer_empty_fallback_used") is True:
            observed.update(observed_sanitizer_empty_fallback_row())
        elif path == REPLACEMENT_PATH_STRICT_SOCIAL:
            observed.update(observed_social_fallback_row())
        observed["fem_runtime_lineage_events"] = build_fem_runtime_lineage_events(fem)
        projection_record = attribution_record_from_replay_projection(observed, replacement_path=path)
        if projection_record is not None:
            records.append(projection_record)

        if drift_row is not None:
            classifications = classify_replay_failure(
                scenario_id="bs1_baseline",
                turn_index=0,
                observed_turn=observed,
                drift_rows=[drift_row],
            )
            for classification in classifications:
                classification_record = attribution_record_from_failure_classification(
                    classification,
                    replacement_path=path,
                    observed_turn=observed,
                )
                if classification_record is not None:
                    records.append(classification_record)

    opening_fail_closed = attribution_record_from_fem(
        fail_closed_opening_fem_meta(final_route="replaced", opening_fallback_failed_closed=True),
        replacement_path=REPLACEMENT_PATH_OPENING_FALLBACK,
    )
    if opening_fail_closed is not None:
        records.append(opening_fail_closed)

    return records


def _field_improvement_delta(
    before_counts: Mapping[str, int],
    after_counts: Mapping[str, int],
) -> dict[str, int]:
    return {
        field: int(before_counts.get(field, 0)) - int(after_counts.get(field, 0))
        for field in REQUIRED_ATTRIBUTION_FIELDS
    }


def render_bs5_projection_convergence_report_md(
    *,
    before_completeness: Mapping[str, Any],
    after_completeness: Mapping[str, Any],
    before_path_report: Mapping[str, Mapping[str, Any]],
    after_path_report: Mapping[str, Mapping[str, Any]],
    before_records: Sequence[AttributionRecord],
    after_records: Sequence[AttributionRecord],
) -> str:
    """Render BS5 before/after attribution convergence comparison."""
    before_missing = {field: 0 for field in REQUIRED_ATTRIBUTION_FIELDS}
    after_missing = {field: 0 for field in REQUIRED_ATTRIBUTION_FIELDS}
    for record in before_records:
        for field in record.get("missing_fields") or []:
            before_missing[field] = before_missing.get(field, 0) + 1
    for record in after_records:
        for field in record.get("missing_fields") or []:
            after_missing[field] = after_missing.get(field, 0) + 1
    field_delta = _field_improvement_delta(before_missing, after_missing)

    lines = [
        "# BS5 Projection Convergence Report",
        "",
        "> Read-side attribution completeness before (BS1 baseline) vs after BS5 projection convergence.",
        "",
        "## Summary",
        "",
        "| Metric | Before (BS1) | After (BS5) | Delta |",
        "|---|---:|---:|---:|",
        f"| Strict completeness | {before_completeness['strict_completeness_pct']}% | "
        f"{after_completeness['strict_completeness_pct']}% | "
        f"{round(after_completeness['strict_completeness_pct'] - before_completeness['strict_completeness_pct'], 2)} |",
        f"| Resolved completeness | {before_completeness['resolved_completeness_pct']}% | "
        f"{after_completeness['resolved_completeness_pct']}% | "
        f"{round(after_completeness['resolved_completeness_pct'] - before_completeness['resolved_completeness_pct'], 2)} |",
        f"| Strict complete records | {before_completeness['strict_complete_records']}/{before_completeness['total_records']} | "
        f"{after_completeness['strict_complete_records']}/{after_completeness['total_records']} | "
        f"{after_completeness['strict_complete_records'] - before_completeness['strict_complete_records']:+d} |",
        f"| Resolved complete records | {before_completeness['resolved_complete_records']}/{before_completeness['total_records']} | "
        f"{after_completeness['resolved_complete_records']}/{after_completeness['total_records']} | "
        f"{after_completeness['resolved_complete_records'] - before_completeness['resolved_complete_records']:+d} |",
        "",
        "## Field-Level Improvements",
        "",
        "| Field | Missing before | Missing after | Slots recovered |",
        "|---|---:|---:|---:|",
    ]
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        lines.append(
            f"| `{field}` | {before_missing[field]} | {after_missing[field]} | {field_delta[field]:+d} |"
        )
    lines.extend(
        [
            "",
            "## Path-Level Improvements (resolved complete)",
            "",
            "| Replacement path | Before complete | After complete | Delta |",
            "|---|---:|---:|---:|",
        ]
    )
    for path in REPLACEMENT_PATHS:
        before_stats = before_path_report.get(path) or {}
        after_stats = after_path_report.get(path) or {}
        before_complete = int(before_stats.get("complete") or 0)
        after_complete = int(after_stats.get("complete") or 0)
        lines.append(f"| {path} | {before_complete} | {after_complete} | {after_complete - before_complete:+d} |")
    lines.append("")
    return "\n".join(lines)


def write_bs5_projection_convergence_report(
    output_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Compare BS1 baseline metrics against current inventory corpus."""
    after_records = build_baseline_attribution_corpus()
    after_completeness = calculate_attribution_completeness(after_records)
    after_path_report = build_replacement_path_attribution_report(after_records)

    before_completeness = dict(BS1_BASELINE_COMPLETENESS)
    before_path_report = {
        path: {
            "total": stats.get("total", 0),
            "complete": stats.get("complete", 0),
        }
        for path, stats in after_path_report.items()
    }
    # BS1 path complete counts from baseline artifact snapshot.
    bs1_path_complete = {
        "visibility replacement": 0,
        "first mention replacement": 0,
        "referential replacement": 0,
        "sealed replacement": 0,
        "response type replacement": 0,
        "sanitizer replacement": 0,
        "repair mutation": 0,
        "opening fallback": 3,
        "strict social replacement": 0,
    }
    for path, complete in bs1_path_complete.items():
        if path in before_path_report:
            before_path_report[path]["complete"] = complete

    before_missing_counts = dict(BS1_BASELINE_MISSING_FIELD_TOTALS)
    after_missing_counts = {field: 0 for field in REQUIRED_ATTRIBUTION_FIELDS}
    for record in after_records:
        for field in record.get("missing_fields") or []:
            after_missing_counts[field] = after_missing_counts.get(field, 0) + 1

    markdown = render_bs5_projection_convergence_report_md(
        before_completeness=before_completeness,
        after_completeness=after_completeness,
        before_path_report=before_path_report,
        after_path_report=after_path_report,
        before_records=after_records,
        after_records=after_records,
    )
    # Replace field-level table body with BS1 snapshot-backed counts.
    field_delta = _field_improvement_delta(before_missing_counts, after_missing_counts)
    lines = markdown.splitlines()
    field_section_start = lines.index("## Field-Level Improvements")
    path_section_start = lines.index("## Path-Level Improvements (resolved complete)")
    rebuilt = lines[: field_section_start + 4]
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        rebuilt.append(
            f"| `{field}` | {before_missing_counts[field]} | {after_missing_counts[field]} | {field_delta[field]:+d} |"
        )
    rebuilt.append("")
    rebuilt.extend(lines[path_section_start:])
    markdown = "\n".join(rebuilt) + "\n"

    target = Path(output_path or "artifacts/bs5_projection_convergence_report.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return before_completeness, after_completeness, markdown


def write_baseline_attribution_report(
    output_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], str]:
    """Generate baseline completeness metrics and write the markdown report."""
    records = build_baseline_attribution_corpus()
    completeness = calculate_attribution_completeness(records)
    path_report = build_replacement_path_attribution_report(records)
    markdown = render_baseline_attribution_report_md(
        completeness=completeness,
        path_report=path_report,
        records=records,
    )
    target = Path(output_path or "artifacts/bs_attribution_baseline_report.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return completeness, path_report, markdown


def render_bs4_producer_stamp_report_md(
    *,
    bs1_completeness: Mapping[str, Any],
    bs5_completeness: Mapping[str, Any],
    bs4_completeness: Mapping[str, Any],
    bs1_missing: Mapping[str, int],
    bs5_missing: Mapping[str, int],
    bs4_missing: Mapping[str, int],
    bs1_path_report: Mapping[str, Mapping[str, Any]],
    bs5_path_report: Mapping[str, Mapping[str, Any]],
    bs4_path_report: Mapping[str, Mapping[str, Any]],
) -> str:
    """Render BS4 producer stamp before/after comparison against BS1 and BS5 snapshots."""
    lines = [
        "# BS4 Producer Stamp Report",
        "",
        "> Producer-side attribution stamps (repair_kind, owner_bucket) compared against BS1 baseline and BS5 projection convergence.",
        "",
        "## Summary",
        "",
        "| Metric | BS1 | BS5 | BS4 | BS4 vs BS1 | BS4 vs BS5 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for label, key in (
        ("Strict completeness %", "strict_completeness_pct"),
        ("Resolved completeness %", "resolved_completeness_pct"),
        ("Strict complete records", "strict_complete_records"),
        ("Resolved complete records", "resolved_complete_records"),
    ):
        bs1_val = bs1_completeness[key]
        bs5_val = bs5_completeness[key]
        bs4_val = bs4_completeness[key]
        if "pct" in key:
            delta1 = round(bs4_val - bs1_val, 2)
            delta5 = round(bs4_val - bs5_val, 2)
        else:
            delta1 = bs4_val - bs1_val
            delta5 = bs4_val - bs5_val
        lines.append(f"| {label} | {bs1_val} | {bs5_val} | {bs4_val} | {delta1:+} | {delta5:+} |")
    lines.extend(
        [
            "",
            "## Field-Level Missing Slots",
            "",
            "| Field | BS1 missing | BS5 missing | BS4 missing | BS4 vs BS1 | BS4 vs BS5 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for field in REQUIRED_ATTRIBUTION_FIELDS:
        bs1_m = int(bs1_missing.get(field, 0))
        bs5_m = int(bs5_missing.get(field, 0))
        bs4_m = int(bs4_missing.get(field, 0))
        lines.append(
            f"| `{field}` | {bs1_m} | {bs5_m} | {bs4_m} | {bs1_m - bs4_m:+d} | {bs5_m - bs4_m:+d} |"
        )
    lines.extend(
        [
            "",
            "## Path-Level Resolved Complete",
            "",
            "| Replacement path | BS1 | BS5 | BS4 | BS4 vs BS1 | BS4 vs BS5 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for path in REPLACEMENT_PATHS:
        bs1_c = int((bs1_path_report.get(path) or {}).get("complete") or 0)
        bs5_c = int((bs5_path_report.get(path) or {}).get("complete") or 0)
        bs4_c = int((bs4_path_report.get(path) or {}).get("complete") or 0)
        lines.append(f"| {path} | {bs1_c} | {bs5_c} | {bs4_c} | {bs4_c - bs1_c:+d} | {bs4_c - bs5_c:+d} |")
    lines.append("")
    return "\n".join(lines)


def _missing_field_totals(records: Sequence[AttributionRecord]) -> dict[str, int]:
    counts = {field: 0 for field in REQUIRED_ATTRIBUTION_FIELDS}
    for record in records:
        for field in record.get("missing_fields") or []:
            counts[field] = counts.get(field, 0) + 1
    return counts


def write_bs4_producer_stamp_report(
    output_path: str | Path | None = None,
) -> tuple[dict[str, Any], str]:
    """Compare BS4 producer-stamped corpus against frozen BS1 and BS5 snapshots."""
    bs4_records = build_baseline_attribution_corpus()
    bs4_completeness = calculate_attribution_completeness(bs4_records)
    bs4_path_report = build_replacement_path_attribution_report(bs4_records)
    bs4_missing = _missing_field_totals(bs4_records)

    bs1_completeness = dict(BS1_BASELINE_COMPLETENESS)
    bs5_completeness = dict(BS5_BASELINE_COMPLETENESS)
    bs1_missing = dict(BS1_BASELINE_MISSING_FIELD_TOTALS)
    bs5_missing = dict(BS5_BASELINE_MISSING_FIELD_TOTALS)

    bs1_path_report = {
        path: {"complete": stats.get("complete", 0), "total": stats.get("total", 0)}
        for path, stats in bs4_path_report.items()
    }
    bs1_path_complete = {
        "visibility replacement": 0,
        "first mention replacement": 0,
        "referential replacement": 0,
        "sealed replacement": 0,
        "response type replacement": 0,
        "sanitizer replacement": 0,
        "repair mutation": 0,
        "opening fallback": 3,
        "strict social replacement": 0,
    }
    for path, complete in bs1_path_complete.items():
        if path in bs1_path_report:
            bs1_path_report[path]["complete"] = complete

    bs5_path_report = dict(bs1_path_report)
    bs5_path_complete = {
        "visibility replacement": 4,
        "first mention replacement": 4,
        "referential replacement": 4,
        "sealed replacement": 0,
        "response type replacement": 5,
        "sanitizer replacement": 9,
        "repair mutation": 0,
        "opening fallback": 6,
        "strict social replacement": 5,
    }
    for path, complete in bs5_path_complete.items():
        if path in bs5_path_report:
            bs5_path_report[path]["complete"] = complete

    markdown = render_bs4_producer_stamp_report_md(
        bs1_completeness=bs1_completeness,
        bs5_completeness=bs5_completeness,
        bs4_completeness=bs4_completeness,
        bs1_missing=bs1_missing,
        bs5_missing=bs5_missing,
        bs4_missing=bs4_missing,
        bs1_path_report=bs1_path_report,
        bs5_path_report=bs5_path_report,
        bs4_path_report=bs4_path_report,
    )
    target = Path(output_path or "artifacts/bs4_producer_stamp_report.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return bs4_completeness, markdown
