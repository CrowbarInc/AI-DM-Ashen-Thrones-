"""Split-owner acceptance matrix, FEM projection, and matrix assertions (CG-2).

**Authority:** owns matrix row definitions and projection helpers only.
Registry: ``docs/audits/CG_failure_classification_authority_registry.md``"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, NamedTuple

from game.attribution_read_views import (
    OPENING_FAIL_CLOSED_CONTENT_OWNER,
    OPENING_FALLBACK_CONTENT_OWNER,
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    OPENING_FALLBACK_SELECTION_OWNER,
    SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_FALLBACK_SELECTION_OWNER,
    SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
    SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD,
    SANITIZER_TRACE_SELECTION_OWNER_SHORT,
    SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
    SEALED_FALLBACK_MODULE_CONTENT_OWNER,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
    SEALED_FALLBACK_SELECTION_OWNER,
    SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
    STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
    UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
    VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
    VISIBILITY_FALLBACK_SELECTION_OWNER,
)
from game.final_emission_replay_projection import (
    FIRST_MENTION_HARD_REPLACEMENT,
    REFERENTIAL_CLARITY_HARD_REPLACEMENT,
    SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
    SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
    SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
    SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
    SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
    SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
    VISIBILITY_HARD_REPLACEMENT,
)
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
from tests.helpers.replay_observed_row_fixtures import SyntheticObservedRowProfile
from tests.helpers.failure_classification_builders import (
    exact_value_drift_row,
    observed_opening_family_split_owner_row,
    observed_referential_local_substitution_classifier_row,
    observed_sanitizer_split_owner_row,
    observed_sealed_family_split_owner_row,
    observed_upstream_fast_split_owner_row,
    observed_visibility_family_hard_replacement_row,
    opening_family_fallback_selected_lineage_event,
    sanitizer_fallback_selected_lineage_event,
    sealed_family_fallback_selected_lineage_event,
    upstream_fast_fallback_selected_lineage_event,
    visibility_family_fallback_selected_lineage_event,
)

# --- BU15 cross-family split-owner acceptance matrix (canonical owner literals) ---


class SplitOwnerAcceptanceRow(NamedTuple):
    """One accepted split-owner fallback family row for cross-surface alignment checks."""

    matrix_id: str
    family: str
    event_kind: str
    fallback_kind: str | None
    mutation_kind: str | None
    fallback_selection_owner: str | None
    fallback_content_owner: str | None
    owner_bucket_field: str | None
    owner_bucket: str | None
    repair_kind: str | None
    stage: str | None
    dashboard_case_id: str | None


def split_owner_acceptance_matrix_rows() -> tuple[SplitOwnerAcceptanceRow, ...]:
    """Return the canonical BU15 split-owner acceptance matrix in stable order."""
    return SPLIT_OWNER_ACCEPTANCE_MATRIX


def split_owner_acceptance_matrix_row_ids() -> tuple[str, ...]:
    """Return stable matrix row ids for parametrized tests."""
    return tuple(row.matrix_id for row in SPLIT_OWNER_ACCEPTANCE_MATRIX)


SPLIT_OWNER_ACCEPTANCE_MATRIX: tuple[SplitOwnerAcceptanceRow, ...] = (
    SplitOwnerAcceptanceRow(
        matrix_id="scene_opening",
        family="opening",
        event_kind="fallback_selected",
        fallback_kind="scene_opening",
        mutation_kind=None,
        fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=OPENING_FALLBACK_CONTENT_OWNER,
        owner_bucket_field="opening_fallback_owner_bucket",
        owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        repair_kind="opening_deterministic_fallback",
        stage="gate",
        dashboard_case_id="scene_opening_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="opening_failed_closed",
        family="opening",
        event_kind="fallback_selected",
        fallback_kind="opening_failed_closed",
        mutation_kind=None,
        fallback_selection_owner=OPENING_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=OPENING_FAIL_CLOSED_CONTENT_OWNER,
        owner_bucket_field="opening_fallback_owner_bucket",
        owner_bucket=OPENING_FALLBACK_OWNER_SEALED_GATE,
        repair_kind="opening_deterministic_fallback_failed_closed",
        stage="gate",
        dashboard_case_id="opening_failed_closed_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="visibility_enforcement",
        family="visibility",
        event_kind="fallback_selected",
        fallback_kind=VISIBILITY_HARD_REPLACEMENT,
        mutation_kind=None,
        fallback_selection_owner=VISIBILITY_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="visibility_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind="visibility_enforcement",
        stage="gate",
        dashboard_case_id="visibility_enforcement_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="first_mention_enforcement",
        family="visibility",
        event_kind="fallback_selected",
        fallback_kind=FIRST_MENTION_HARD_REPLACEMENT,
        mutation_kind=None,
        fallback_selection_owner=VISIBILITY_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="visibility_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind="first_mention_enforcement",
        stage="gate",
        dashboard_case_id="first_mention_enforcement_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="referential_clarity_enforcement",
        family="visibility",
        event_kind="fallback_selected",
        fallback_kind=REFERENTIAL_CLARITY_HARD_REPLACEMENT,
        mutation_kind=None,
        fallback_selection_owner=VISIBILITY_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        owner_bucket_field="visibility_fallback_owner_bucket",
        owner_bucket=VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        repair_kind="referential_clarity_enforcement",
        stage="gate",
        dashboard_case_id="referential_clarity_enforcement_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="referential_local_substitution",
        family="visibility",
        event_kind="mutation",
        fallback_kind=None,
        mutation_kind="referential_clarity_local_substitution_mutation",
        fallback_selection_owner=None,
        fallback_content_owner=None,
        owner_bucket_field="visibility_fallback_owner_bucket",
        owner_bucket=VISIBILITY_FALLBACK_OWNER_STRICT_SOCIAL_VISIBILITY,
        repair_kind="referential_clarity_local_substitution",
        stage="gate",
        dashboard_case_id="referential_local_substitution_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sanitizer_empty_output",
        family="sanitizer",
        event_kind="fallback_selected",
        fallback_kind="sanitizer_empty_output",
        mutation_kind=None,
        fallback_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        owner_bucket_field=None,
        owner_bucket=None,
        repair_kind="sanitizer_empty_output",
        stage="sanitizer",
        dashboard_case_id="sanitizer_empty_output_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sanitizer_strict_social",
        family="sanitizer",
        event_kind="fallback_selected",
        fallback_kind="sanitizer_strict_social",
        mutation_kind=None,
        fallback_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
        owner_bucket_field=None,
        owner_bucket=None,
        repair_kind="strict_social_repair",
        stage="sanitizer",
        dashboard_case_id="sanitizer_strict_social_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="upstream_fast_fallback",
        family="upstream_fast",
        event_kind="fallback_selected",
        fallback_kind="upstream_fast_fallback",
        mutation_kind=None,
        fallback_selection_owner=UPSTREAM_FAST_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=UPSTREAM_FAST_FALLBACK_CONTENT_OWNER,
        owner_bucket_field=None,
        owner_bucket="retry",
        repair_kind=None,
        stage="retry",
        dashboard_case_id="upstream_fast_fallback_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_social_interlocutor",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_SOCIAL_INTERLOCUTOR,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=STRICT_SOCIAL_FALLBACK_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_social_interlocutor_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_passive_scene_pressure",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_PASSIVE_SCENE_PRESSURE,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_passive_scene_pressure_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_npc_pursuit_neutral",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_NPC_PURSUIT_NEUTRAL,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_npc_pursuit_neutral_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_anti_reset_continuation",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_ANTI_RESET_CONTINUATION,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_anti_reset_continuation_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_global_scene",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_GLOBAL_SCENE,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_MODULE_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_global_scene_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_unknown_replacement",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind=SEALED_REPLACEMENT_SUBKIND_UNKNOWN,
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_UNKNOWN_NONE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id="sealed_unknown_replacement_split_owner",
    ),
    SplitOwnerAcceptanceRow(
        matrix_id="sealed_or_global_replacement_legacy",
        family="sealed",
        event_kind="fallback_selected",
        fallback_kind="sealed_or_global_replacement",
        mutation_kind=None,
        fallback_selection_owner=SEALED_FALLBACK_SELECTION_OWNER,
        fallback_content_owner=SEALED_FALLBACK_UNKNOWN_CONTENT_OWNER,
        owner_bucket_field="sealed_fallback_owner_bucket",
        owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        repair_kind=None,
        stage="gate",
        dashboard_case_id=None,
    ),
)


_SEALED_MATRIX_FINAL_EMITTED_SOURCES: dict[str, str] = {
    "sealed_social_interlocutor": "social_interlocutor_minimal_fallback",
    "sealed_passive_scene_pressure": "passive_scene_pressure_fallback",
    "sealed_npc_pursuit_neutral": "npc_pursuit_neutral_fallback",
    "sealed_anti_reset_continuation": "anti_reset_local_continuation_fallback",
    "sealed_global_scene": "global_scene_fallback",
    "sealed_unknown_replacement": "unclassified_terminal_fallback",
    "sealed_or_global_replacement_legacy": "global_scene_fallback",
}

# BU17: legacy matrix rows stay in the acceptance matrix for classifier vocabulary only.
SPLIT_OWNER_LEGACY_MATRIX_ROWS: dict[str, str] = {
    "sealed_or_global_replacement_legacy": (
        "Synthetic classifier vocabulary only; production FEM maps global_scene_fallback "
        "to sealed_global_scene_fallback. Dashboard and FEM projection probes intentionally "
        "excluded; classifier coverage remains in "
        "test_failure_classifier.py::test_failure_classifier_accepts_sealed_family_runtime_lineage_split_owners."
    ),
}

# Rows validated via synthetic observed-row builders only; production FEM maps to modern subkinds.
SPLIT_OWNER_FEM_PROJECTION_EXCLUSIONS: dict[str, str] = {
    matrix_id: reason
    for matrix_id, reason in SPLIT_OWNER_LEGACY_MATRIX_ROWS.items()
}

_VISIBILITY_HARD_REPLACEMENT_FEM_DEFAULTS: dict[str, Any] = {
    "final_route": "replaced",
    "final_emitted_source": "global_scene_fallback",
    "visibility_fallback_pool": "global_scene_narrative",
    "visibility_fallback_kind": "narrative_safe_fallback",
}


def split_owner_matrix_row_by_id(matrix_id: str) -> SplitOwnerAcceptanceRow:
    """Return one canonical matrix row by id."""
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        if row.matrix_id == matrix_id:
            return row
    raise KeyError(f"unknown split-owner matrix row: {matrix_id!r}")


def split_owner_matrix_legacy(row: SplitOwnerAcceptanceRow) -> bool:
    """Return True when a matrix row is synthetic-only legacy vocabulary."""
    return row.matrix_id in SPLIT_OWNER_LEGACY_MATRIX_ROWS


def split_owner_fem_projection_excluded(row: SplitOwnerAcceptanceRow) -> bool:
    """Return True when production FEM projection is intentionally out of scope for a row."""
    return split_owner_matrix_legacy(row)


def split_owner_fem_projection_exclusion_reason(row: SplitOwnerAcceptanceRow) -> str | None:
    """Return the documented exclusion reason when FEM projection is out of scope."""
    return SPLIT_OWNER_FEM_PROJECTION_EXCLUSIONS.get(row.matrix_id)


def split_owner_fem_meta_from_matrix_row(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build synthetic FEM/meta dict for production replay projection from a matrix row."""
    if split_owner_fem_projection_excluded(row):
        reason = split_owner_fem_projection_exclusion_reason(row)
        raise ValueError(f"matrix row {row.matrix_id!r} has no FEM projection fixture: {reason}")

    from tests.helpers.golden_replay_fixtures import fem_payload
    from tests.helpers.opening_fallback_evidence import (
        fail_closed_opening_fem_meta,
        successful_opening_fem_meta,
    )

    if row.matrix_id == "scene_opening":
        return successful_opening_fem_meta(
            response_type_repair_kind=row.repair_kind,
            fallback_temporal_frame="first_impression",
        )
    if row.matrix_id == "opening_failed_closed":
        return fail_closed_opening_fem_meta(
            opening_recovered_via_fallback=True,
            fallback_family_used="scene_opening",
        )
    if row.matrix_id == "visibility_enforcement":
        return fem_payload(
            **_VISIBILITY_HARD_REPLACEMENT_FEM_DEFAULTS,
            visibility_replacement_applied=True,
            visibility_fallback_owner_bucket=row.owner_bucket,
            producer_repair_kind=row.repair_kind,
        )
    if row.matrix_id == "first_mention_enforcement":
        return fem_payload(
            **_VISIBILITY_HARD_REPLACEMENT_FEM_DEFAULTS,
            first_mention_replacement_applied=True,
            visibility_fallback_owner_bucket=row.owner_bucket,
            producer_repair_kind=row.repair_kind,
        )
    if row.matrix_id == "referential_clarity_enforcement":
        return fem_payload(
            **_VISIBILITY_HARD_REPLACEMENT_FEM_DEFAULTS,
            referential_clarity_replacement_applied=True,
            visibility_fallback_owner_bucket=row.owner_bucket,
            producer_repair_kind=row.repair_kind,
        )
    if row.matrix_id == "referential_local_substitution":
        return fem_payload(
            final_route="accept_candidate",
            referential_clarity_local_substitution_applied=True,
            referential_clarity_local_substitution_token="she",
            referential_clarity_local_substitution_replacement="The Tavern Runner",
            visibility_fallback_owner_bucket=row.owner_bucket,
            producer_repair_kind=row.repair_kind,
        )
    if row.matrix_id == "sanitizer_empty_output":
        return fem_payload(
            final_emitted_source="generated_candidate",
            sanitizer_empty_fallback_used=True,
            sanitizer_empty_fallback_source="upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
            sanitizer_empty_fallback_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
            final_emission_mutation_lineage=[
                "pre_gate_sanitizer",
                "sanitizer_empty_fallback",
                "finalize_packaging",
            ],
        )
    if row.matrix_id == "sanitizer_strict_social":
        return fem_payload(
            final_emitted_source="generated_candidate",
            strict_social_active=True,
            sanitizer_strict_social_fallback_used=True,
            sanitizer_strict_social_selection_owner=SANITIZER_FALLBACK_SELECTION_OWNER,
            sanitizer_strict_social_prose_owner=SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
            sanitizer_strict_social_source="social_fallback_line_for_sanitizer.empty_output",
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source=None,
            upstream_prepared_emission_reject_reason=None,
        )
    if row.matrix_id == "upstream_fast_fallback":
        return fem_payload(
            final_emitted_source="generated_candidate",
            fallback_provenance_trace={
                "source": "fallback",
                "stage": "fallback_selector",
                "content_fingerprint": "abc123",
                "gate_exit_vs_selector_match": True,
            },
        )
    if row.family == "sealed":
        return fem_payload(
            final_route="replaced",
            final_emitted_source=_SEALED_MATRIX_FINAL_EMITTED_SOURCES[row.matrix_id],
            sealed_fallback_owner_bucket=row.owner_bucket,
            realization_fallback_family="gate_terminal_repair",
        )
    raise ValueError(f"unsupported matrix row for FEM projection: {row.matrix_id!r}")


def split_owner_sanitizer_projection_metadata(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build sanitizer_trace metadata for golden replay sanitizer-family matrix rows."""
    if row.matrix_id == "sanitizer_empty_output":
        return {
            "sanitizer_trace": {
                "sanitizer_boundary_mode": "strip_only",
                "sanitizer_empty_fallback_used": True,
                "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                "sanitizer_empty_fallback_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                SANITIZER_EMPTY_FALLBACK_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
            }
        }
    if row.matrix_id == "sanitizer_strict_social":
        return {
            "sanitizer_trace": {
                "sanitizer_lineage_mode": "strip_only",
                "sanitizer_strict_social_fallback_used": True,
                "sanitizer_strict_social_selection_owner": SANITIZER_FALLBACK_SELECTION_OWNER,
                "sanitizer_strict_social_prose_owner": SANITIZER_STRICT_SOCIAL_CONTENT_OWNER,
                SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
                SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
                "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
            }
        }
    raise ValueError(f"unsupported sanitizer matrix row: {row.matrix_id!r}")


def split_owner_projection_turn_kwargs(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build kwargs for :func:`project_synthetic_turn` from a canonical matrix row."""
    if split_owner_fem_projection_excluded(row):
        reason = split_owner_fem_projection_exclusion_reason(row)
        raise ValueError(f"matrix row {row.matrix_id!r} has no projection turn fixture: {reason}")

    from tests.helpers.golden_replay_fixtures import minimal_gm_output_payload

    kwargs: dict[str, Any] = {
        "scenario_id": f"matrix_fem_{row.matrix_id}",
        "gm_text": {
            "scene_opening": "The road opens under morning light.",
            "opening_failed_closed": "The road opens under sealed gate light.",
            "referential_local_substitution": "The Tavern Runner says she will return.",
            "sanitizer_strict_social": 'The runner says, "No names."',
        }.get(row.matrix_id, "Synthetic split-owner projection line."),
    }
    fem_meta = split_owner_fem_meta_from_matrix_row(row)
    if row.family == "sanitizer":
        kwargs["payload"] = minimal_gm_output_payload(
            fem_meta=fem_meta,
            metadata=split_owner_sanitizer_projection_metadata(row),
        )
        kwargs["player_text"] = "Ask the runner." if row.matrix_id == "sanitizer_strict_social" else "Wait."
        kwargs["resolution"] = {"kind": "question" if row.matrix_id == "sanitizer_strict_social" else "observe"}
    else:
        kwargs["fem_meta"] = fem_meta
        if row.matrix_id == "upstream_fast_fallback":
            kwargs["player_text"] = "Wait."
            kwargs["resolution"] = {"kind": "observe"}
    return kwargs


def project_split_owner_matrix_row(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Project one matrix row through production golden replay FEM/replay projection."""
    from tests.helpers.golden_replay_fixtures import project_synthetic_turn

    return project_synthetic_turn(**split_owner_projection_turn_kwargs(row))


def assert_split_owner_matrix_fem_projection(
    row: SplitOwnerAcceptanceRow,
    observed: Mapping[str, Any],
) -> None:
    """Assert production FEM/replay projection matches the canonical matrix row."""
    if row.owner_bucket_field is not None and row.owner_bucket is not None:
        assert observed.get(row.owner_bucket_field) == row.owner_bucket

    if row.event_kind == "mutation":
        event = next(
            item
            for item in observed.get("runtime_lineage_events") or []
            if item.get("event_kind") == "mutation" and item.get("mutation_kind") == row.mutation_kind
        )
        assert_split_owner_matrix_lineage_event(row, event)
        return

    event = next(
        item
        for item in observed.get("runtime_lineage_events") or []
        if item.get("event_kind") == "fallback_selected"
    )
    assert_split_owner_matrix_lineage_event(row, event)


def split_owner_lineage_event_from_matrix_row(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build one runtime lineage event from a canonical matrix row."""
    if row.event_kind == "mutation":
        return make_runtime_lineage_event(
            event_kind="mutation",
            stage=row.stage or "gate",
            owner=OPENING_FALLBACK_SELECTION_OWNER,
            mutation_kind=row.mutation_kind,
            source="She",
        )
    if row.family == "opening":
        authorship = (
            OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
            if row.fallback_kind == "scene_opening"
            else None
        )
        return opening_family_fallback_selected_lineage_event(
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            fallback_owner_bucket=str(row.owner_bucket),
            fallback_authorship_source=authorship,
            repair_kind=row.repair_kind,
        )
    if row.family == "visibility" and row.event_kind == "fallback_selected":
        return visibility_family_fallback_selected_lineage_event(
            fallback_kind=str(row.fallback_kind),
            repair_kind=str(row.repair_kind),
            fallback_owner_bucket=str(row.owner_bucket),
            fallback_content_owner=str(row.fallback_content_owner),
        )
    if row.family == "sanitizer":
        return sanitizer_fallback_selected_lineage_event(
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            repair_kind=row.repair_kind,
        )
    if row.family == "upstream_fast":
        return upstream_fast_fallback_selected_lineage_event()
    if row.family == "sealed":
        return sealed_family_fallback_selected_lineage_event(
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            fallback_owner_bucket=str(row.owner_bucket),
        )
    raise ValueError(f"unsupported matrix row: {row.matrix_id!r}")


def split_owner_observed_row_from_matrix_row(
    row: SplitOwnerAcceptanceRow,
    *,
    profile: SyntheticObservedRowProfile = "classifier_probe",
) -> dict[str, Any]:
    """Build one classifier/dashboard observed row from a canonical matrix row."""
    dashboard_overrides: dict[str, Any] = {}
    if profile == "dashboard_probe":
        if row.matrix_id == "sanitizer_strict_social":
            dashboard_overrides = {
                SANITIZER_STRICT_SOCIAL_SELECTION_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_SELECTION_OWNER_SHORT,
                SANITIZER_STRICT_SOCIAL_PROSE_OWNER_TRACE_SHORT_FIELD: SANITIZER_TRACE_STRICT_SOCIAL_PROSE_OWNER_SHORT,
            }
        elif row.matrix_id == "sanitizer_empty_output":
            dashboard_overrides = {
                "sanitizer_lineage_mode": "strip_only",
                "sanitizer_lineage_empty_fallback_used": True,
            }

    if row.matrix_id == "referential_local_substitution":
        return observed_referential_local_substitution_classifier_row(
            profile=profile,
            visibility_fallback_owner_bucket=str(row.owner_bucket),
            **dashboard_overrides,
        )
    if row.family == "opening":
        return observed_opening_family_split_owner_row(
            profile=profile,
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            opening_fallback_owner_bucket=str(row.owner_bucket),
            **dashboard_overrides,
        )
    if row.family == "visibility" and row.fallback_kind == VISIBILITY_HARD_REPLACEMENT:
        return observed_visibility_family_hard_replacement_row(
            profile=profile,
            visibility_replacement_applied=True,
            fallback_kind=row.fallback_kind,
            repair_kind=str(row.repair_kind),
            visibility_fallback_owner_bucket=str(row.owner_bucket),
            fallback_content_owner=str(row.fallback_content_owner),
            **dashboard_overrides,
        )
    if row.family == "visibility" and row.fallback_kind == FIRST_MENTION_HARD_REPLACEMENT:
        return observed_visibility_family_hard_replacement_row(
            profile=profile,
            first_mention_replacement_applied=True,
            fallback_kind=row.fallback_kind,
            repair_kind=str(row.repair_kind),
            visibility_fallback_owner_bucket=str(row.owner_bucket),
            fallback_content_owner=str(row.fallback_content_owner),
            **dashboard_overrides,
        )
    if row.family == "visibility" and row.fallback_kind == REFERENTIAL_CLARITY_HARD_REPLACEMENT:
        return observed_visibility_family_hard_replacement_row(
            profile=profile,
            referential_clarity_replacement_applied=True,
            fallback_kind=row.fallback_kind,
            repair_kind=str(row.repair_kind),
            visibility_fallback_owner_bucket=str(row.owner_bucket),
            fallback_content_owner=str(row.fallback_content_owner),
            **dashboard_overrides,
        )
    if row.family == "sanitizer":
        return observed_sanitizer_split_owner_row(
            profile=profile,
            fallback_kind=str(row.fallback_kind),
            fallback_content_owner=str(row.fallback_content_owner),
            repair_kind=row.repair_kind,
            **dashboard_overrides,
        )
    if row.family == "upstream_fast":
        return observed_upstream_fast_split_owner_row(profile=profile, **dashboard_overrides)
    if row.family == "sealed":
        return observed_sealed_family_split_owner_row(
            profile=profile,
            fallback_kind=str(row.fallback_kind),
            final_emitted_source=_SEALED_MATRIX_FINAL_EMITTED_SOURCES[row.matrix_id],
            fallback_content_owner=str(row.fallback_content_owner),
            sealed_fallback_owner_bucket=str(row.owner_bucket),
            **dashboard_overrides,
        )
    raise ValueError(f"unsupported matrix row: {row.matrix_id!r}")


def split_owner_matrix_classifier_drift_row(row: SplitOwnerAcceptanceRow) -> dict[str, Any]:
    """Build the replay drift row used by classifier/dashboard matrix probes."""
    if row.event_kind == "mutation":
        return exact_value_drift_row(
            "referential_clarity_local_substitution_applied",
            expected=False,
            actual=True,
            reason=f"{row.matrix_id} referential local substitution drift probe",
        )
    return exact_value_drift_row(
        "fallback_content_owner",
        expected=row.fallback_selection_owner,
        actual=row.fallback_content_owner,
        reason=f"{row.matrix_id} split owner projection changed",
    )


def assert_split_owner_matrix_lineage_event(
    row: SplitOwnerAcceptanceRow,
    event: Mapping[str, Any],
) -> None:
    """Assert one lineage event matches the canonical matrix row."""
    assert event.get("event_kind") == row.event_kind
    if row.stage is not None:
        assert event.get("stage") == row.stage
    if row.event_kind == "mutation":
        assert event.get("mutation_kind") == row.mutation_kind
        assert event.get("owner") == OPENING_FALLBACK_SELECTION_OWNER
        return
    assert event.get("fallback_kind") == row.fallback_kind
    assert event.get("fallback_selection_owner") == row.fallback_selection_owner
    assert event.get("fallback_content_owner") == row.fallback_content_owner
    if row.owner_bucket is not None and event.get("fallback_owner_bucket") is not None:
        assert event.get("fallback_owner_bucket") == row.owner_bucket
    if row.repair_kind is not None and event.get("repair_kind") is not None:
        assert event.get("repair_kind") == row.repair_kind


def assert_split_owner_matrix_classifier_row(
    row: SplitOwnerAcceptanceRow,
    classified_row: Mapping[str, Any],
) -> None:
    """Assert one classifier/dashboard row matches the canonical matrix row."""
    if row.event_kind == "mutation":
        if row.owner_bucket_field is not None:
            assert classified_row.get(row.owner_bucket_field) == row.owner_bucket
        if row.repair_kind is not None:
            assert classified_row.get("repair_kind") == row.repair_kind
        return
    assert classified_row.get("fallback_selection_owner") == row.fallback_selection_owner
    assert classified_row.get("fallback_content_owner") == row.fallback_content_owner
    if row.owner_bucket_field is not None:
        assert classified_row.get(row.owner_bucket_field) == row.owner_bucket
    if row.repair_kind is not None:
        assert classified_row.get("repair_kind") == row.repair_kind


def render_split_owner_acceptance_matrix_report() -> str:
    """Render a concise markdown report of the canonical BU15/BU16/BU17/BU18/BU19 matrix."""
    from tests.helpers.failure_classification_dashboard_expectations import (
        SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES,
        split_owner_matrix_controlled_failure_cases,
        split_owner_sealed_matrix_rows_requiring_dashboard_probe,
    )

    lines = [
        "# BU15/BU16/BU17/BU18/BU19 Split-Owner Acceptance Matrix",
        "",
        "Canonical cross-family owner literals shared by classifier, dashboard, golden replay FEM "
        "projection, runtime lineage summary, and attribution inventory tests.",
        "",
        "| matrix_id | family | event_kind | fallback/mutation kind | selection_owner | content_owner | "
        "owner_bucket_field | owner_bucket | repair_kind | dashboard_case_id | fem_projection |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        kind = row.fallback_kind or row.mutation_kind or ""
        fem_status = "excluded" if split_owner_fem_projection_excluded(row) else "matrix_fem"
        lines.append(
            f"| {row.matrix_id} | {row.family} | {row.event_kind} | {kind} | "
            f"{row.fallback_selection_owner or ''} | {row.fallback_content_owner or ''} | "
            f"{row.owner_bucket_field or ''} | {row.owner_bucket or ''} | "
            f"{row.repair_kind or ''} | {row.dashboard_case_id or ''} | {fem_status} |"
        )
    lines.append("")
    lines.append(f"Total rows: {len(SPLIT_OWNER_ACCEPTANCE_MATRIX)}")
    lines.append(f"Dashboard probes: {len(split_owner_matrix_controlled_failure_cases())}")
    sealed_dashboard_rows = split_owner_sealed_matrix_rows_requiring_dashboard_probe()
    lines.append(
        f"Sealed subkind dashboard parity: {sum(1 for row in sealed_dashboard_rows if row.dashboard_case_id)}"
        f"/{len(sealed_dashboard_rows)} non-legacy rows"
    )
    if SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES:
        lines.append("")
        lines.append("## Dashboard case id aliases (BU18)")
        for matrix_id, (case_id, rationale) in SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES.items():
            lines.append(f"- `{matrix_id}` -> `{case_id}`: {rationale}")
    if SPLIT_OWNER_LEGACY_MATRIX_ROWS:
        lines.append("")
        lines.append("## Legacy matrix rows (BU17 synthetic-only)")
        for matrix_id, reason in SPLIT_OWNER_LEGACY_MATRIX_ROWS.items():
            lines.append(f"- `{matrix_id}`: {reason}")
    if SPLIT_OWNER_FEM_PROJECTION_EXCLUSIONS:
        lines.append("")
        lines.append("## FEM projection exclusions")
        for matrix_id, reason in SPLIT_OWNER_FEM_PROJECTION_EXCLUSIONS.items():
            lines.append(f"- `{matrix_id}`: {reason}")
    lines.extend(split_owner_acceptance_matrix_report_footer_lines())
    return "\n".join(lines)


def split_owner_acceptance_matrix_report_footer_lines() -> list[str]:
    """Return maintainer footer lines appended to the checked-in matrix report."""
    return [
        "",
        "## Split-owner matrix change workflow (BU22)",
        "",
        "Canonical source: `SPLIT_OWNER_ACCEPTANCE_MATRIX` in "
        "`tests/helpers/failure_classification_split_owner.py`. "
        "Full checklist: `docs/audits/README.md`.",
        "",
        "1. Update `SPLIT_OWNER_ACCEPTANCE_MATRIX` (no production emission changes for matrix-only edits).",
        "2. Update dashboard evidence cells only if dashboard strings changed "
        "(`tests/test_failure_dashboard_controlled_failures.py`).",
        "3. Regenerate and validate: "
        "`python scripts/refresh_split_owner_acceptance_matrix.py` "
        "(or `make split-owner-matrix-refresh`).",
        "4. Partial modes: `--write-report-only`, `--check-only`, `--skip-pytest`.",
        "5. Run focused classifier/dashboard/projection tests only when behavior changed.",
        "",
        "## Maintainer commands (BU20/BU21/BU23/BU24)",
        "",
        "Full refresh (Windows-native; default):",
        "",
        "```bash",
        "python scripts/refresh_split_owner_acceptance_matrix.py",
        "```",
        "",
        "Unix/mac/Git Bash equivalent:",
        "",
        "```bash",
        "make split-owner-matrix-refresh",
        "```",
        "",
        "Report only / check only:",
        "",
        "```bash",
        "python scripts/refresh_split_owner_acceptance_matrix.py --write-report-only",
        "python scripts/refresh_split_owner_acceptance_matrix.py --check-only",
        "python scripts/refresh_split_owner_acceptance_matrix.py --skip-pytest",
        "```",
        "",
        "Contract gate only (also in CI convergence-checks and default fast lane):",
        "",
        "```bash",
        "python scripts/check_split_owner_acceptance_matrix.py",
        "# or",
        "make split-owner-matrix-check",
        "# or",
        "python -m pytest tests/test_split_owner_acceptance_matrix_contract.py -q -m split_owner_matrix_contract",
        "```",
    ]


SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH = "docs/audits/BU15_split_owner_acceptance_matrix.md"
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_TOTAL_ROWS = 16
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS = 15
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_FEM_PROJECTION_ROWS = 15
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_LEGACY_ONLY_ROWS = 1
SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_SEALED_NON_LEGACY_DASHBOARD_ROWS = 6


def split_owner_acceptance_matrix_counts() -> dict[str, int]:
    """Return live split-owner matrix row counts for contract/CI gates."""
    from tests.helpers.failure_classification_dashboard_expectations import (
        split_owner_matrix_controlled_failure_cases,
        split_owner_sealed_matrix_rows_requiring_dashboard_probe,
    )

    rows = SPLIT_OWNER_ACCEPTANCE_MATRIX
    legacy_rows = [row for row in rows if split_owner_matrix_legacy(row)]
    dashboard_rows = [row for row in rows if row.dashboard_case_id is not None]
    fem_rows = [row for row in rows if not split_owner_fem_projection_excluded(row)]
    sealed_dashboard_rows = split_owner_sealed_matrix_rows_requiring_dashboard_probe()
    return {
        "total_rows": len(rows),
        "dashboard_covered_rows": len(dashboard_rows),
        "fem_projection_rows": len(fem_rows),
        "legacy_only_rows": len(legacy_rows),
        "dashboard_probes": len(split_owner_matrix_controlled_failure_cases()),
        "sealed_non_legacy_dashboard_rows": sum(
            1 for row in sealed_dashboard_rows if row.dashboard_case_id is not None
        ),
    }


def split_owner_acceptance_matrix_report_text(*, repo_root: Path | None = None) -> str:
    """Read the checked-in split-owner acceptance matrix report from disk."""
    from pathlib import Path as _Path

    root = repo_root if repo_root is not None else _Path(__file__).resolve().parents[2]
    report_path = root / SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH
    return report_path.read_text(encoding="utf-8").replace("\r\n", "\n")


def split_owner_acceptance_matrix_classifier_builder_misalignments() -> list[str]:
    """Return classifier/dashboard builder drift messages without running classification."""
    misalignments: list[str] = []
    for row in SPLIT_OWNER_ACCEPTANCE_MATRIX:
        try:
            observed = split_owner_observed_row_from_matrix_row(row)
            drift = split_owner_matrix_classifier_drift_row(row)
        except Exception as exc:  # pragma: no cover - defensive contract surface
            misalignments.append(f"{row.matrix_id!r} builder failed: {exc}")
            continue
        if not observed:
            misalignments.append(f"{row.matrix_id!r} observed row builder returned empty payload")
        if not drift.get("field_path"):
            misalignments.append(f"{row.matrix_id!r} classifier drift row missing field_path")
        if row.event_kind != "mutation" and row.dashboard_case_id is not None:
            event = (observed.get("runtime_lineage_events") or [None])[0]
            if not isinstance(event, dict):
                misalignments.append(f"{row.matrix_id!r} dashboard probe missing runtime_lineage_events[0]")
            else:
                try:
                    assert_split_owner_matrix_lineage_event(row, event)
                except AssertionError as exc:
                    misalignments.append(f"{row.matrix_id!r} embedded lineage drift: {exc}")
    return misalignments


def split_owner_acceptance_matrix_contract_misalignments(
    *,
    repo_root: Path | None = None,
) -> list[str]:
    """Return split-owner matrix contract drift messages; empty when BU20-locked."""
    from pathlib import Path as _Path

    misalignments: list[str] = []

    from tests.helpers.failure_classification_dashboard_expectations import (
        SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES,
        split_owner_matrix_dashboard_case_id_misalignments,
    )

    if SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES:
        misalignments.append(
            "SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES must remain empty after BU19; "
            f"got {sorted(SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES)!r}"
        )

    misalignments.extend(split_owner_matrix_dashboard_case_id_misalignments())

    counts = split_owner_acceptance_matrix_counts()
    expected_counts = {
        "total_rows": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_TOTAL_ROWS,
        "dashboard_covered_rows": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS,
        "fem_projection_rows": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_FEM_PROJECTION_ROWS,
        "legacy_only_rows": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_LEGACY_ONLY_ROWS,
        "dashboard_probes": SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS,
        "sealed_non_legacy_dashboard_rows": (
            SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_SEALED_NON_LEGACY_DASHBOARD_ROWS
        ),
    }
    for key, expected in expected_counts.items():
        actual = counts[key]
        if actual != expected:
            misalignments.append(f"{key} expected {expected}, got {actual}")

    if counts["dashboard_probes"] != counts["dashboard_covered_rows"]:
        misalignments.append(
            "dashboard_probes must equal dashboard_covered_rows; "
            f"probes={counts['dashboard_probes']} covered={counts['dashboard_covered_rows']}"
        )
    if counts["fem_projection_rows"] + counts["legacy_only_rows"] != counts["total_rows"]:
        misalignments.append(
            "fem_projection_rows + legacy_only_rows must equal total_rows; "
            f"fem={counts['fem_projection_rows']} legacy={counts['legacy_only_rows']} "
            f"total={counts['total_rows']}"
        )

    legacy_matrix_ids = {
        row.matrix_id for row in SPLIT_OWNER_ACCEPTANCE_MATRIX if split_owner_matrix_legacy(row)
    }
    if legacy_matrix_ids != set(SPLIT_OWNER_LEGACY_MATRIX_ROWS):
        misalignments.append(
            "legacy matrix rows must match SPLIT_OWNER_LEGACY_MATRIX_ROWS; "
            f"matrix={sorted(legacy_matrix_ids)!r} registry={sorted(SPLIT_OWNER_LEGACY_MATRIX_ROWS)!r}"
        )

    rendered = render_split_owner_acceptance_matrix_report()
    on_disk = split_owner_acceptance_matrix_report_text(repo_root=repo_root)
    if rendered != on_disk:
        root = repo_root if repo_root is not None else _Path(__file__).resolve().parents[2]
        misalignments.append(
            f"{SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH} is out of date; "
            f"regenerate with render_split_owner_acceptance_matrix_report() "
            f"(repo root {root})"
        )

    misalignments.extend(split_owner_acceptance_matrix_classifier_builder_misalignments())
    return misalignments


def assert_split_owner_acceptance_matrix_contract(*, repo_root: Path | None = None) -> None:
    """Assert BU20 split-owner matrix/report/dashboard/FEM/classifier builder contract."""
    misalignments = split_owner_acceptance_matrix_contract_misalignments(repo_root=repo_root)
    if misalignments:
        joined = "\n".join(f"- {item}" for item in misalignments)
        raise AssertionError(f"split-owner acceptance matrix contract drift:\n{joined}")


