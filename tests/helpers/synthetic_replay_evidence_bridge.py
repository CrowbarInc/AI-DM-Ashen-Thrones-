"""CF7 — synthetic replay row / classifier evidence bridge registry.

Read-side inventory distinguishing synthetic observed-row builders from live replay
projection. Does not write rows or change replay/classifier behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from tests.failure_classification_contract import CLASSIFIER_EVIDENCE_EXTENSION_FIELDS
from tests.helpers.golden_replay_projection import (
    protected_classifier_evidence_field_paths,
    protected_observation_flat_field_paths,
)
from tests.helpers.replay_observed_row_fixtures import synthetic_classifier_probe_overlay_paths

EvidenceKind = Literal[
    "live_only",
    "synthetic_only",
    "shared",
    "overlay_derived",
    "diagnostic_only",
]

SYNTHETIC_PROFILE_ONLY_PATHS: frozenset[str] = frozenset(
    {
        "scenario_id",
        "final_text_hash",
        "raw_signal_presence",
        "normalized_signal_presence",
    }
)

DASHBOARD_PROFILE_ONLY_PATHS: frozenset[str] = frozenset(
    {
        "raw_signal_presence",
        "normalized_signal_presence",
    }
)

LIVE_PROJECTION_ENTRY_POINTS: tuple[str, ...] = (
    "tests.helpers.golden_replay_projection::project_turn_observation",
    "tests.helpers.golden_replay_fixtures::project_synthetic_turn",
    "tests.helpers.golden_replay_fixtures::observed_turn_from_gate_output",
)

ACCEPTANCE_AUTHORITY = "live_replay_projection"


@dataclass(frozen=True)
class SyntheticReplayBuilder:
    """One synthetic or hybrid observed-row builder."""

    builder_id: str
    owner_module: str
    consumer: str
    purpose: str
    row_kind: str
    entry_point: str
    projected_fields: tuple[str, ...]
    notes: str = ""


@dataclass(frozen=True)
class ClassifierEvidenceBridgeRow:
    """One classifier-visible field evidence chain row."""

    field: str
    live_source: str
    synthetic_source: str
    classifier_consumer: str
    evidence_kind: EvidenceKind
    runtime_owner: str
    projection_owner: str
    synthetic_owner: str
    classifier_owner: str
    notes: str = ""


def synthetic_replay_builder_inventory() -> tuple[SyntheticReplayBuilder, ...]:
    """Return documented synthetic/hybrid observed-row builders."""
    overlay = tuple(sorted(synthetic_classifier_probe_overlay_paths()))
    flat_protected = tuple(sorted(protected_observation_flat_field_paths()))
    return (
        SyntheticReplayBuilder(
            builder_id="synthetic_observed_replay_row",
            owner_module="tests.helpers.replay_observed_row_fixtures",
            consumer="classifier probes; dashboard controlled failures; CF2/CF5 governance",
            purpose="Canonical AO4 factory — schema defaults + probe overlay + profile defaults",
            row_kind="synthetic",
            entry_point="synthetic_observed_replay_row",
            projected_fields=flat_protected + overlay,
            notes="Does not call project_turn_observation; not acceptance authority.",
        ),
        SyntheticReplayBuilder(
            builder_id="observed_failure_row",
            owner_module="tests.helpers.replay_observed_row_fixtures",
            consumer="failure_classifier.py; failure_classification_sync",
            purpose="Classifier probe profile alias",
            row_kind="synthetic",
            entry_point="observed_failure_row → synthetic_observed_replay_row(classifier_probe)",
            projected_fields=flat_protected + overlay,
        ),
        SyntheticReplayBuilder(
            builder_id="observed_dashboard_probe_row",
            owner_module="tests.helpers.replay_observed_row_fixtures",
            consumer="failure_dashboard_fixtures; controlled failure probes",
            purpose="Dashboard probe profile with empty presence dict defaults",
            row_kind="synthetic",
            entry_point="observed_dashboard_probe_row → synthetic_observed_replay_row(dashboard_probe)",
            projected_fields=flat_protected + overlay + ("raw_signal_presence", "normalized_signal_presence"),
        ),
        SyntheticReplayBuilder(
            builder_id="failure_classification_sync_specialty_rows",
            owner_module="tests.helpers.failure_classification_sync",
            consumer="classifier contract sync; split-owner matrix probes",
            purpose="Domain-specific synthetic overlays (opening, sealed, sanitizer, visibility, matrix)",
            row_kind="synthetic_overlay",
            entry_point="observed_*_row helpers → _observed_row → synthetic factory",
            projected_fields=("domain-specific protected + lineage fields",),
            notes="15+ specialty builders; matrix rows may also use live FEM via project_split_owner_matrix_row.",
        ),
        SyntheticReplayBuilder(
            builder_id="project_synthetic_turn",
            owner_module="tests.helpers.golden_replay_fixtures",
            consumer="split-owner FEM parity; golden replay integration",
            purpose="Live projection adapter over minimal synthetic turn payload",
            row_kind="live_projection",
            entry_point="project_synthetic_turn → project_turn_observation(minimal_turn_payload)",
            projected_fields=flat_protected,
            notes="Acceptance-shaped output via canonical assembler; not a hand-built row.",
        ),
        SyntheticReplayBuilder(
            builder_id="observed_turn_from_gate_output",
            owner_module="tests.helpers.golden_replay_fixtures",
            consumer="direct-seam golden replay; fallback projection tests",
            purpose="Live projection from gate gm_output dict",
            row_kind="live_projection",
            entry_point="observed_turn_from_gate_output → project_turn_observation",
            projected_fields=flat_protected,
            notes="Acceptance authority path for fixture-backed scenarios.",
        ),
        SyntheticReplayBuilder(
            builder_id="synthetic_rerun_turn",
            owner_module="tests.helpers.replay_observed_row_fixtures",
            consumer="rerun drift scorecard report tests",
            purpose="Partial turn dict for scorecard comparison only",
            row_kind="partial_synthetic",
            entry_point="synthetic_rerun_turn",
            projected_fields=(
                "turn_index",
                "turn_id",
                "route_kind",
                "selected_speaker_id",
                "fallback_family",
                "final_text",
                "runtime_lineage_events",
            ),
            notes="Not a classifier observed row; must not be used as classify_replay_failure input.",
        ),
        SyntheticReplayBuilder(
            builder_id="protected_speaker_failure_turn",
            owner_module="tests.helpers.replay_observed_row_fixtures",
            consumer="protected replay failure dashboard reports",
            purpose="Hand-built speaker-failure narrative for report rendering",
            row_kind="synthetic_diagnostic",
            entry_point="protected_speaker_failure_turn",
            projected_fields=flat_protected + ("source_path", "branch_id", "turn_id", "runtime_lineage_events"),
            notes="Uses schema defaults + manual trace; diagnostic report fixture only.",
        ),
        SyntheticReplayBuilder(
            builder_id="owner_drift_classification_fixture",
            owner_module="tests.helpers.replay_drift_taxonomy",
            consumer="owner drift report tests",
            purpose="Classifier output row built from synthetic observed + drift",
            row_kind="classifier_output",
            entry_point="classify_replay_failure(observed_failure_row(), drift_rows=[...])",
            projected_fields=("FailureClassification row fields",),
            notes="Output artifact, not observed-turn input.",
        ),
    )


def synthetic_builder_by_id(builder_id: str) -> SyntheticReplayBuilder | None:
    for builder in synthetic_replay_builder_inventory():
        if builder.builder_id == builder_id:
            return builder
    return None


def _overlay_bridge_rows() -> list[ClassifierEvidenceBridgeRow]:
    overlay_paths = synthetic_classifier_probe_overlay_paths()
    rows: list[ClassifierEvidenceBridgeRow] = []
    projection_owner = "tests.helpers.golden_replay_projection"
    for path in sorted(overlay_paths):
        if path == "trace":
            rows.append(
                ClassifierEvidenceBridgeRow(
                    field="trace",
                    live_source="project_turn_observation(payload/snap debug trace)",
                    synthetic_source="replay_observed_row_fixtures._CLASSIFIER_PROBE_OVERLAY",
                    classifier_consumer="failure_classifier route/speaker rules",
                    evidence_kind="overlay_derived",
                    runtime_owner="game.final_emission_gate / trace assembly",
                    projection_owner=projection_owner,
                    synthetic_owner="tests.helpers.replay_observed_row_fixtures",
                    classifier_owner="tests.helpers.failure_classifier",
                    notes="Injected canonical_entry + social_contract_trace without live runtime.",
                )
            )
            continue
        rows.append(
            ClassifierEvidenceBridgeRow(
                field=path,
                live_source=f"project_turn_observation extraction for {path!r}",
                synthetic_source="replay_observed_row_fixtures._CLASSIFIER_PROBE_OVERLAY",
                classifier_consumer="failure_classifier / dashboard evidence copy",
                evidence_kind="overlay_derived",
                runtime_owner="runtime FEM/trace/snap producers",
                projection_owner=projection_owner,
                synthetic_owner="tests.helpers.replay_observed_row_fixtures",
                classifier_owner="tests.helpers.failure_classifier",
            )
        )
    return rows


def _protected_default_bridge_rows() -> list[ClassifierEvidenceBridgeRow]:
    rows: list[ClassifierEvidenceBridgeRow] = []
    overlay = synthetic_classifier_probe_overlay_paths()
    for path in sorted(protected_observation_flat_field_paths()):
        if path in overlay or path in SYNTHETIC_PROFILE_ONLY_PATHS:
            continue
        rows.append(
            ClassifierEvidenceBridgeRow(
                field=path,
                live_source="project_turn_observation protected extraction",
                synthetic_source="observed_projection_schema_defaults → protected_observation_default_row",
                classifier_consumer="classifier when in protected_classifier_evidence_field_paths",
                evidence_kind="shared",
                runtime_owner="field-family runtime producer",
                projection_owner="tests.helpers.golden_replay_projection_extractors",
                synthetic_owner="tests.helpers.golden_replay_projection_fields",
                classifier_owner="tests.helpers.failure_classifier",
                notes="Neutral None/False/'' defaults mask absent producers in synthetic rows (CF2 risk).",
            )
        )
    return rows


def _profile_synthetic_bridge_rows() -> list[ClassifierEvidenceBridgeRow]:
    return [
        ClassifierEvidenceBridgeRow(
            field="scenario_id",
            live_source="replay runner scenario_id stamp",
            synthetic_source="profile defaults: probe / controlled_probe",
            classifier_consumer="classification row scenario_id",
            evidence_kind="synthetic_only",
            runtime_owner="tests.helpers.golden_replay",
            projection_owner="project_turn_observation envelope",
            synthetic_owner="tests.helpers.replay_observed_row_fixtures",
            classifier_owner="tests.helpers.failure_classifier",
        ),
        ClassifierEvidenceBridgeRow(
            field="final_text_hash",
            live_source="golden_text_hash(projected final_text)",
            synthetic_source="profile literals: hash123 / probehash",
            classifier_consumer="classification row final_text_hash",
            evidence_kind="synthetic_only",
            runtime_owner="N/A (derived from final_text)",
            projection_owner="tests.helpers.golden_replay_projection_fields",
            synthetic_owner="tests.helpers.replay_observed_row_fixtures",
            classifier_owner="tests.helpers.failure_classifier",
        ),
        ClassifierEvidenceBridgeRow(
            field="raw_signal_presence",
            live_source="project_turn_observation _build_projection_status",
            synthetic_source="dashboard_probe profile injects {}",
            classifier_consumer="dashboard evidence / projection diagnostics",
            evidence_kind="synthetic_only",
            runtime_owner="FEM/normalization producers",
            projection_owner="tests.helpers.golden_replay_projection_extractors",
            synthetic_owner="tests.helpers.replay_observed_row_fixtures",
            classifier_owner="tests.helpers.failure_dashboard_report",
            notes="classifier_probe profile omits key unless override.",
        ),
        ClassifierEvidenceBridgeRow(
            field="normalized_signal_presence",
            live_source="project_turn_observation _build_projection_status",
            synthetic_source="dashboard_probe profile injects {}",
            classifier_consumer="dashboard evidence / projection diagnostics",
            evidence_kind="synthetic_only",
            runtime_owner="FEM/normalization producers",
            projection_owner="tests.helpers.golden_replay_projection_extractors",
            synthetic_owner="tests.helpers.replay_observed_row_fixtures",
            classifier_owner="tests.helpers.failure_dashboard_report",
        ),
    ]


def _extension_field_bridge_rows() -> list[ClassifierEvidenceBridgeRow]:
    rows: list[ClassifierEvidenceBridgeRow] = []
    for field in sorted(CLASSIFIER_EVIDENCE_EXTENSION_FIELDS):
        rows.append(
            ClassifierEvidenceBridgeRow(
                field=field,
                live_source="runtime lineage / split-owner stamps on live projection",
                synthetic_source="specialty observed_* builders or matrix overlays",
                classifier_consumer="failure_classifier optional evidence + dashboard manifest",
                evidence_kind="overlay_derived",
                runtime_owner="game.final_emission_replay_projection / attribution views",
                projection_owner="tests.helpers.golden_replay_projection",
                synthetic_owner="tests.helpers.failure_classification_sync",
                classifier_owner="tests.helpers.failure_classifier",
                notes="Not flat protected paths; copied via _copy_manifest_observed_evidence.",
            )
        )
    return rows


def classifier_evidence_bridge_matrix() -> tuple[ClassifierEvidenceBridgeRow, ...]:
    """Return CF7 evidence matrix rows for classifier-visible fields."""
    rows: list[ClassifierEvidenceBridgeRow] = []
    rows.extend(_overlay_bridge_rows())
    rows.extend(_protected_default_bridge_rows())
    rows.extend(_profile_synthetic_bridge_rows())
    rows.extend(_extension_field_bridge_rows())
    return tuple(rows)


def classifier_evidence_bridge_row(field: str) -> ClassifierEvidenceBridgeRow | None:
    for row in classifier_evidence_bridge_matrix():
        if row.field == field:
            return row
    return None


def live_only_classifier_evidence_paths() -> frozenset[str]:
    """Protected classifier evidence paths with no synthetic default backing."""
    protected_overlap = protected_classifier_evidence_field_paths()
    overlay = synthetic_classifier_probe_overlay_paths()
    synthetic_only = SYNTHETIC_PROFILE_ONLY_PATHS | DASHBOARD_PROFILE_ONLY_PATHS
    return frozenset(
        path
        for path in protected_overlap
        if path not in overlay and path not in synthetic_only
    )


def synthetic_row_is_acceptance_authority() -> bool:
    """Synthetic hand-built rows are never acceptance authority (CF7 invariant)."""
    return False
