from __future__ import annotations

import importlib.util
from pathlib import Path

from tests.helpers.golden_replay import _observed_turn
from tests.helpers.golden_replay_fixtures import (
    fem_payload,
    minimal_gm_output_payload,
    minimal_turn_payload,
    observed_turn_from_gate_output,
    project_synthetic_turn,
)
from tests.helpers.golden_replay_projection import (
    REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS,
    dual_fallback_family_replay_precedence_surface,
    lookup_observation_path,
    project_replay_fallback_family_from_fem,
    project_turn_observation,
    protected_field_paths,
    protected_observation_drift_bucket,
    protected_observation_extraction_registry,
    protected_observation_field_paths,
    protected_observation_field_registry,
    protected_path_representation_errors,
)


def _load_manifest_tool():
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "refresh_protected_replay_manifest",
        root / "tools" / "refresh_protected_replay_manifest.py",
    )
    assert spec is not None and spec.loader is not None
    refresh_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refresh_mod)
    return refresh_mod


def test_golden_replay_projection_adapter_wires_observed_turn():
    turn_payload = minimal_turn_payload(
        scenario_id="projection_adapter",
        gm_text="Rain falls on the gate road.",
        fem_meta=fem_payload(
            response_type_required="neutral_narration",
            final_emitted_source="upstream_prepared_emission",
        ),
    )
    via_adapter = project_turn_observation(turn_payload)
    via_wrapper = _observed_turn(
        scenario_id=str(turn_payload["scenario_id"]),
        snap=dict(turn_payload["snap"]),
        payload=dict(turn_payload["payload"]),
    )
    assert via_adapter == via_wrapper
    paths = protected_field_paths()
    registry_paths = protected_observation_field_paths()
    assert protected_field_paths() == registry_paths
    assert len(paths) == len(set(paths))
    assert protected_observation_drift_bucket("fallback_family") == "structural_drift"
    assert protected_observation_drift_bucket("scaffold_leakage") == "semantic_drift"
    assert "final_emitted_source" in paths
    assert "scaffold_leakage" in paths
    assert "route_kind" in paths
    assert paths == tuple(sorted(set(paths)))


def test_golden_replay_dual_family_projection_prefers_diegetic_fallback_family_used() -> None:
    """Read-side ``fallback_family`` prefers diegetic taxonomy when both FEM fields are present."""
    fem = {
        "fallback_family_used": "scene_opening",
        "realization_fallback_family": "upstream_prepared_emission",
    }
    assert project_replay_fallback_family_from_fem(fem) == "scene_opening"

    turn = project_turn_observation(
        minimal_turn_payload(
            scenario_id="dual_family_diegetic_first",
            gm_text="Rain on the gate road.",
            fem_meta=fem,
        )
    )
    assert turn["fallback_family"] == "scene_opening"
    assert "fallback_family_used" in turn["fem_raw_keys"]
    assert "realization_fallback_family" in turn["fem_raw_keys"]


def test_golden_replay_dual_family_projection_falls_back_to_realization_when_diegetic_absent() -> None:
    """Read-side projection uses governed provenance only when diegetic field is absent."""
    fem = {"realization_fallback_family": "upstream_prepared_emission"}
    assert project_replay_fallback_family_from_fem(fem) == "upstream_prepared_emission"

    turn = project_turn_observation(
        minimal_turn_payload(
            scenario_id="dual_family_realization_fallback",
            gm_text="The notice board creaks.",
            fem_meta=fem,
        )
    )
    assert turn["fallback_family"] == "upstream_prepared_emission"


def test_golden_replay_dual_family_projection_returns_none_when_both_absent() -> None:
    """Read-side projector returns None when neither FEM family field is present."""
    assert project_replay_fallback_family_from_fem({}) is None
    assert project_replay_fallback_family_from_fem({"final_emitted_source": "generated_candidate"}) is None

    turn = project_turn_observation(
        minimal_turn_payload(
            scenario_id="dual_family_both_absent",
            gm_text="The lane stays quiet.",
            fem_meta={"final_emitted_source": "generated_candidate"},
        )
    )
    assert turn["fallback_family"] is None
    assert "fallback_family" in turn["unavailable"]


def test_golden_replay_dual_family_precedence_surface_documents_read_side_rule() -> None:
    surface = dual_fallback_family_replay_precedence_surface()
    assert surface["prefer_field"] == "fallback_family_used"
    assert surface["fallback_field"] == "realization_fallback_family"
    assert surface["precedence_keys"] == list(REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS)
    assert surface["read_side_only"] is True
    assert project_replay_fallback_family_from_fem(
        {"fallback_family_used": "social", "realization_fallback_family": "gate_terminal_repair"}
    ) == "social"


def test_golden_replay_dual_family_projection_does_not_rewrite_raw_fem_fields() -> None:
    """Projection must not collapse or rewrite runtime FEM dual-family stamps."""
    raw_fem = {
        "fallback_family_used": "scene_opening",
        "realization_fallback_family": "upstream_prepared_emission",
        "final_emitted_source": "opening_deterministic_fallback",
    }
    payload = minimal_gm_output_payload(fem_meta=raw_fem)
    project_turn_observation(
        minimal_turn_payload(
            scenario_id="dual_family_no_rewrite",
            gm_text="Torchlight on wet stone.",
            payload=payload,
        )
    )
    stored = payload["gm_output"]["_final_emission_meta"]
    assert stored["fallback_family_used"] == "scene_opening"
    assert stored["realization_fallback_family"] == "upstream_prepared_emission"


def test_observed_turn_from_gate_output_projects_direct_seam_fields() -> None:
    """Direct-seam helper uses canonical projection and supports extra assertion fields."""
    raw_fem = {
        "fallback_family_used": "scene_opening",
        "realization_fallback_family": "upstream_prepared_emission",
        "final_emitted_source": "opening_deterministic_fallback",
    }
    gm_output = {
        "player_facing_text": "Rain on the gate.",
        "_final_emission_meta": dict(raw_fem),
    }
    turn = observed_turn_from_gate_output(
        scenario_id="direct_seam_helper_probe",
        gm_output=gm_output,
        extra_fields={"dialogue_plan_valid": True},
    )
    assert turn["final_text"] == "Rain on the gate."
    assert turn["final_emitted_source"] == "opening_deterministic_fallback"
    assert turn["fallback_family"] == "scene_opening"
    assert "fallback_family_used" in turn["fem_raw_keys"]
    assert "realization_fallback_family" in turn["fem_raw_keys"]
    assert turn["dialogue_plan_valid"] is True
    stored = gm_output["_final_emission_meta"]
    assert stored["fallback_family_used"] == "scene_opening"
    assert stored["realization_fallback_family"] == "upstream_prepared_emission"


def test_protected_replay_manifest_matches_observation_registry():
    refresh_mod = _load_manifest_tool()
    manifest_text = refresh_mod.MANIFEST_PATH.read_text(encoding="utf-8")
    expected = refresh_mod.render_generated_section()
    current = refresh_mod.extract_generated_section(manifest_text)

    assert current is not None, "protected replay manifest is missing generated protected_field_paths section"
    assert current == expected, (
        "protected replay manifest generated section is out of date; "
        "run: python tools/refresh_protected_replay_manifest.py --write"
    )
    assert refresh_mod.manifest_section_is_current(manifest_text)

    paths = tuple(sorted({field.path for field in protected_observation_field_registry()}))
    assert str(len(paths)) in current
    for field in protected_observation_field_registry():
        assert f"| `{field.path}` | `{field.drift_bucket}` |" in current


def test_ak5_every_protected_path_is_projected_or_marked_unavailable():
    """Each protected registry path must appear on the observed turn or in unavailable."""
    sparse = project_turn_observation(
        minimal_turn_payload(
            scenario_id="ak5_sparse_projection",
            gm_text="Rain on the gate road.",
        )
    )
    assert protected_path_representation_errors(sparse) == []

    rich_payload = minimal_gm_output_payload(
        fem_meta=fem_payload(
            final_emitted_source="upstream_prepared_emission",
            response_type_required="dialogue_response",
            response_type_repair_used=True,
            response_type_repair_kind="dialogue_minimal_repair",
            fallback_temporal_frame="present",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
            fallback_family_used="social",
            realization_fallback_family="upstream_prepared_emission",
            opening_recovered_via_fallback=False,
            opening_fallback_authorship_source="upstream_prepared_opening_fallback",
            sealed_fallback_owner_bucket="unknown-none",
            visibility_fallback_owner_bucket="unknown-none",
        ),
        metadata={
            "sanitizer_trace": {
                "sanitizer_lineage_mode": "strip_only",
                "sanitizer_empty_fallback_used": True,
                "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                "sanitizer_empty_fallback_owner": "output_sanitizer",
                "sanitizer_lineage_changed_count": 1,
                "sanitizer_lineage_dropped_count": 0,
                "sanitizer_lineage_empty_fallback_used": True,
                "sanitizer_lineage_legacy_rewrite_active": False,
                "sanitizer_strict_social_fallback_used": False,
            }
        },
    )
    rich_payload["sanitizer_debug"] = [
        {"event": "strip_only_dropped_rewrite_candidate", "sentence": "Planner scaffold."},
    ]
    rich_payload["debug_traces"] = [
        {
            "canonical_entry": {
                "target_actor_id": "runner",
                "target_source": "social",
                "reason": "direct_vocative",
            },
            "turn_trace": {
                "social_contract_trace": {"route_selected": "dialogue"},
            },
        }
    ]
    rich = project_synthetic_turn(
        scenario_id="ak5_rich_projection",
        gm_text="The runner says the patrol moved east.",
        player_text="Ask the runner.",
        resolution={"kind": "question", "social": {"npc_id": "runner"}},
        payload=rich_payload,
    )
    assert protected_path_representation_errors(rich) == []


def test_ak5_protected_observation_field_paths_are_sorted_unique():
    paths = protected_observation_field_paths()
    assert paths == tuple(sorted(set(paths)))
    assert len(paths) == len(protected_observation_field_registry())


def test_ao1_protected_extraction_registry_matches_observation_registry():
    registry_paths = {field.path for field in protected_observation_field_registry()}
    extraction_paths = set(protected_observation_extraction_registry())
    assert extraction_paths == registry_paths
    assert len(extraction_paths) == 41


def test_ak5_manifest_generated_section_matches_registry():
    refresh_mod = _load_manifest_tool()
    registry_paths = {field.path: field.drift_bucket for field in protected_observation_field_registry()}
    manifest_paths = refresh_mod._registry_fields_by_path()

    assert set(registry_paths) == set(manifest_paths)
    for path, bucket in registry_paths.items():
        assert manifest_paths[path] == bucket
    assert refresh_mod.manifest_section_is_current(refresh_mod.MANIFEST_PATH.read_text(encoding="utf-8"))


def test_ak5_synthetic_turn_exercises_fem_backed_protected_fields():
    observed = project_synthetic_turn(
        scenario_id="ak5_fem_backed_projection",
        gm_text="The runner confirms the patrol route.",
        resolution={"kind": "question"},
        fem_meta=fem_payload(
            final_emitted_source="upstream_prepared_emission",
            response_type_required="dialogue_response",
            response_type_repair_used=True,
            response_type_repair_kind="dialogue_minimal_repair",
            fallback_temporal_frame="present",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
        ),
    )

    assert observed["final_emitted_source"] == "upstream_prepared_emission"
    assert observed["response_type_required"] == "dialogue_response"
    assert observed["response_type_repair_used"] is True
    assert observed["response_type_repair_kind"] == "dialogue_minimal_repair"
    assert observed["fallback_temporal_frame"] == "present"
    assert observed["upstream_prepared_emission_used"] is True
    assert observed["upstream_prepared_emission_valid"] is True


def test_ak5_synthetic_turn_exercises_sanitizer_backed_protected_fields():
    observed = project_synthetic_turn(
        scenario_id="ak5_sanitizer_backed_projection",
        gm_text="For a breath, the scene stays still.",
        resolution={"kind": "observe"},
        payload={
            **minimal_gm_output_payload(
                fem_meta=fem_payload(final_emitted_source="generated_candidate"),
                metadata={
                    "sanitizer_trace": {
                        "sanitizer_lineage_mode": "strip_only",
                        "sanitizer_empty_fallback_used": True,
                        "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                        "sanitizer_empty_fallback_owner": "output_sanitizer",
                        "sanitizer_lineage_changed_count": 2,
                        "sanitizer_lineage_dropped_count": 1,
                    }
                },
            ),
            "sanitizer_debug": [
                {"event": "strip_only_dropped_rewrite_candidate", "sentence": "Planner scaffold."},
                {"event": "strip_only_dropped_non_diegetic", "sentence": "Validator scaffold."},
            ],
        },
    )

    assert observed["sanitizer_empty_fallback_used"] is True
    assert observed["sanitizer_empty_fallback_source"] == "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text"
    assert observed["sanitizer_empty_fallback_owner"] == "output_sanitizer"
    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_changed_count"] == 2
    assert observed["sanitizer_lineage_dropped_count"] == 1


def test_ak5_complex_projection_contracts_remain_locked():
    """Dual fallback-family, dotted trace lookup, and semantic drift bucket stay explicit."""
    fem = {
        "fallback_family_used": "scene_opening",
        "realization_fallback_family": "upstream_prepared_emission",
    }
    assert project_replay_fallback_family_from_fem(fem) == "scene_opening"

    observed = project_synthetic_turn(
        scenario_id="ak5_complex_projection",
        gm_text="planner scaffold leaked into final text",
        payload={
            **minimal_gm_output_payload(fem_meta=fem_payload(**fem)),
            "debug_traces": [
                {
                    "canonical_entry": {
                        "target_actor_id": "runner",
                        "target_source": "social",
                        "reason": "direct",
                    },
                    "turn_trace": {
                        "social_contract_trace": {"route_selected": "dialogue"},
                    },
                }
            ],
        },
    )

    assert observed["fallback_family"] == "scene_opening"
    assert lookup_observation_path(observed, "trace.canonical_entry.target_actor_id") == "runner"
    assert lookup_observation_path(observed, "trace.canonical_entry.target_source") == "social"
    assert lookup_observation_path(observed, "trace.canonical_entry.reason") == "direct"
    assert lookup_observation_path(observed, "trace.social_contract_trace.route_selected") == "dialogue"
    assert observed["scaffold_leakage"] is True
    assert protected_observation_drift_bucket("scaffold_leakage") == "semantic_drift"
    assert protected_observation_drift_bucket("fallback_family") == "structural_drift"


def test_golden_observed_turn_projects_response_delta_metadata():
    observed = project_synthetic_turn(
        scenario_id="response_delta_projection",
        gm_text="The runner adds a new location lead.",
        fem_meta=fem_payload(
            response_delta_checked=True,
            response_delta_failed=True,
            response_delta_repaired=False,
            response_delta_kind_detected="new_actionable_lead",
            response_delta_echo_overlap_ratio=0.2,
            response_delta_trigger_source="strict_social_answer_pressure",
        ),
    )

    assert observed["response_delta_checked"] is True
    assert observed["response_delta_failed"] is True
    assert observed["response_delta_repaired"] is False
    assert observed["response_delta_kind"] == "new_actionable_lead"
    assert observed["response_delta_echo_overlap_ratio"] == 0.2
    assert observed["response_delta_echo_overlap_band"] == "low"
    assert observed["response_delta_trigger_source"] == "strict_social_answer_pressure"


def test_golden_observed_turn_projects_clean_sanitizer_lineage():
    observed = project_synthetic_turn(
        scenario_id="sanitizer_clean_lineage",
        gm_text="Rain needles across the checkpoint.",
        player_text="Wait.",
        resolution={"kind": "observe"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(final_emitted_source="generated_candidate"),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_lineage_mode": "strip_only",
                    "sanitizer_lineage_changed_count": 0,
                    "sanitizer_lineage_dropped_count": 0,
                    "sanitizer_lineage_empty_fallback_used": False,
                    "sanitizer_lineage_legacy_rewrite_active": False,
                }
            },
        ),
    )

    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_changed_count"] == 0
    assert observed["sanitizer_lineage_dropped_count"] == 0
    assert observed["sanitizer_lineage_empty_fallback_used"] is False
    assert observed["sanitizer_lineage_legacy_rewrite_active"] is False


def test_golden_observed_turn_projects_sanitizer_lineage_from_debug_events():
    observed = project_synthetic_turn(
        scenario_id="sanitizer_debug_lineage",
        gm_text="",
        player_text="Wait.",
        resolution={"kind": "observe"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(final_emitted_source="generated_candidate"),
            metadata={
                "sanitizer_trace": {"sanitizer_boundary_mode": "strip_only"},
                "sanitizer_debug": [
                    {"event": "strip_only_dropped_rewrite_candidate", "sentence": "Validator scaffold."},
                    {"event": "strip_only_dropped_non_diegetic", "sentence": "Planner scaffold."},
                ],
            },
        ),
    )

    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_changed_count"] == 2
    assert observed["sanitizer_lineage_dropped_count"] == 2


def test_golden_observed_turn_projects_legacy_sanitizer_lineage():
    observed = project_synthetic_turn(
        scenario_id="sanitizer_legacy_lineage",
        gm_text="The answer has not formed yet.",
        player_text="Wait.",
        resolution={"kind": "observe"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(final_emitted_source="generated_candidate"),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_lineage_mode": "legacy_sentence_rewrite",
                    "sanitizer_lineage_changed_count": 1,
                    "sanitizer_lineage_dropped_count": 0,
                    "sanitizer_lineage_empty_fallback_used": False,
                    "sanitizer_lineage_legacy_rewrite_active": True,
                }
            },
        ),
    )

    assert observed["sanitizer_lineage_mode"] == "legacy_sentence_rewrite"
    assert observed["sanitizer_lineage_legacy_rewrite_active"] is True
