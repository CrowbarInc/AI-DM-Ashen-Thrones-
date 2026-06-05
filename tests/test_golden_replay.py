from __future__ import annotations

import json

import pytest

from game import storage
from game.api import chat
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import (
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    opening_fallback_owner_bucket_from_meta,
)
from tests.helpers.golden_replay_projection import read_fem_meta_from_gate_output
from game.runtime_lineage_telemetry import make_runtime_lineage_event
from game.final_emission_replay_projection import SEALED_REPLACEMENT_SUBKINDS
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
from game.scenario_spine import (
    ScenarioBranch,
    ScenarioSpine,
    ScenarioTurn,
    scenario_spine_to_dict,
    validate_scenario_spine_definition,
)
from game.scenario_spine_eval import minimal_complete_transcript_turn_meta
from game.models import ChatRequest
from tests.helpers.golden_replay import (
    FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    _observed_turn,
    assert_golden_turn_observation,
    assert_protected_golden_turn_observation,
    classify_golden_drift,
    compare_golden_replay_reruns,
    evaluate_golden_replay_continuity_drift,
    final_text_has_scaffold_leakage,
    format_golden_replay_debug,
    frontier_gate_branch_prompts,
    frontier_gate_branch_turn_ids,
    load_frontier_gate_long_session_spine,
    protected_no_scaffold_expectation,
    protected_route_expectation,
    protected_social_structural_base,
    protected_structural_expectation,
    protected_unavailable_expectation,
    render_golden_replay_markdown_report,
    render_long_session_replay_summary_markdown,
    run_golden_replay,
    summarize_long_session_replay_observations,
)
from tests.helpers.golden_replay_projection import (
    lookup_observation_path,
    project_replay_fallback_family_from_fem,
    dual_fallback_family_replay_precedence_surface,
    REPLAY_FALLBACK_FAMILY_FEM_PRECEDENCE_KEYS,
    project_turn_observation,
    protected_field_paths,
    protected_observation_drift_bucket,
    protected_observation_field_paths,
    protected_observation_field_registry,
    protected_observation_extraction_registry,
    protected_path_representation_errors,
)
from tests.helpers.transcript_runner import (
    new_clean_campaign,
    patch_transcript_storage,
    snapshot_from_chat_payload,
    write_default_bootstrap_scenes,
)
from tests.helpers.failure_dashboard_report import (
    clear_recorded_failure_dashboard_rows,
    clear_recorded_protected_replay_failures,
    clear_recorded_rerun_drift_scorecards,
    recorded_protected_replay_failure_rows,
    record_rerun_drift_scorecard,
    recorded_rerun_drift_scorecards,
    recorded_runtime_lineage_events,
    render_rerun_drift_scorecard_markdown,
    write_rerun_drift_scorecard_artifacts,
    write_rerun_drift_scorecard_artifacts_if_requested,
    write_protected_replay_failure_report_if_present,
)
from tests.helpers.opening_fallback_evidence import (
    fail_closed_opening_fem_meta,
    successful_opening_fem_meta,
    successful_opening_observed_fields,
)
from tests.helpers.dialogue_social_plan import (
    attach_dialogue_social_plan_to_resolution,
    make_valid_dialogue_social_plan,
)
from tests.helpers.block_stu_equivalence_fixtures import locked_runner_contract, stub_strict_social_details
from tests.helpers.gate_equivalence_monkeypatch import (
    patch_build_final_strict_social_response,
    patch_get_speaker_selection_contract,
)
from tests.helpers.opening_fallback_evidence import opening_gm_output
from tests.helpers.strict_social_harness import runner_strict_bundle
from tests.helpers.golden_replay_fixtures import (
    fem_payload,
    gm_response,
    golden_replay_chat_stubs,
    minimal_gm_output_payload,
    minimal_turn_payload,
    observed_turn_from_gate_output,
    project_synthetic_turn,
    seed_frontier_gate_world,
    seed_investigator_runner_world,
    seed_runner_continuity_world,
    seed_runner_guard_world,
    seed_scene_object_investigation_world,
    seed_spine_three_branch_world,
    seed_tavern_patrol_lead_world,
)

pytestmark = [pytest.mark.integration, pytest.mark.golden_replay]

# Ownership note:
# Golden replay owns replay observation and projection contracts. Turn observation
# projection is centralized in ``tests.helpers.golden_replay_projection`` (Cycle T1).
# Repeated route/speaker/fallback/final-emission fields are intentional diagnostic
# locks, not runtime ownership of those subsystems.


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
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "refresh_protected_replay_manifest",
        root / "tools" / "refresh_protected_replay_manifest.py",
    )
    assert spec is not None and spec.loader is not None
    refresh_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refresh_mod)

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


# Cycle AK5 — replay projection schema safety locks (pre-AK1 refactor guards).


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
    import importlib.util
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "refresh_protected_replay_manifest",
        root / "tools" / "refresh_protected_replay_manifest.py",
    )
    assert spec is not None and spec.loader is not None
    refresh_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refresh_mod)

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


def test_golden_expectation_helper_supports_dotted_paths_and_debug_messages():
    turn = {
        "final_text": 'Tavern Runner says, "No names."',
        "resolution_kind": "question",
        "route_kind": "dialogue",
        "selected_speaker_id": "runner",
        "final_emitted_source": "generated_candidate",
        "fallback_family": None,
        "scaffold_leakage": False,
        "unavailable": ["fallback_family"],
        "trace": {
            "canonical_entry": {"target_actor_id": "runner"},
            "social_contract_trace": {"route_selected": "dialogue"},
        },
    }

    assert_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "trace.canonical_entry.target_actor_id"],
            "allow_unavailable": ["fallback_family"],
            "equals": {"trace.canonical_entry.target_actor_id": "runner"},
            "one_of": {"trace.social_contract_trace.route_selected": ["dialogue", "social"]},
            "not_equals": {"final_emitted_source": "global_scene_fallback"},
            "text_must_include": ["Tavern Runner"],
            "text_must_not_include": ["planner"],
            "scaffold_leakage": False,
        },
        debug_context="synthetic debug context",
    )

    with pytest.raises(AssertionError) as exc:
        assert_golden_turn_observation(
            turn,
            {
                "allow_unavailable": ["fallback_family"],
                "equals": {"trace.canonical_entry.target_actor_id": "gate_guard"},
            },
            debug_context="synthetic debug context",
        )
    message = str(exc.value)
    assert "trace.canonical_entry.target_actor_id" in message
    assert "gate_guard" in message
    assert "runner" in message
    assert "synthetic debug context" in message


def test_protected_golden_assertion_failure_records_canonical_report(tmp_path):
    turn = {
        "turn_index": 0,
        "source_path": "data/validation/scenario_spines/synthetic_fixture.json",
        "branch_id": "synthetic_branch",
        "turn_id": "synthetic_turn_01",
        "final_text": 'Gate Guard says, "No names."',
        "route_kind": "dialogue",
        "selected_speaker_id": "guard",
        "final_emitted_source": "generated_candidate",
        "fallback_family": None,
        "scaffold_leakage": False,
        "unavailable": [],
        "runtime_lineage_events": [
            make_runtime_lineage_event(
                event_kind="gate_outcome",
                stage="gate",
                owner="game.final_emission_gate",
                gate_path="accept_unchanged",
            )
        ],
        "trace": {
            "canonical_entry": {"target_actor_id": "runner"},
            "social_contract_trace": {"route_selected": "dialogue"},
        },
    }
    report_path = tmp_path / "replay_failure_report.md"
    clear_recorded_protected_replay_failures()
    try:
        assert write_protected_replay_failure_report_if_present(path=report_path) is None
        with pytest.raises(AssertionError) as exc:
            assert_protected_golden_turn_observation(
                turn,
                {"equals": {"selected_speaker_id": "runner"}},
                scenario_id="synthetic_protected_bridge",
                debug_context="synthetic reporting bridge context",
            )
        assert "golden replay expectation failed: exact value mismatch" in str(exc.value)

        rows = recorded_protected_replay_failure_rows()
        assert len(rows) == 1
        assert rows[0]["scenario_id"] == "synthetic_protected_bridge"
        assert rows[0]["source_path"] == "data/validation/scenario_spines/synthetic_fixture.json"
        assert rows[0]["branch_id"] == "synthetic_branch"
        assert rows[0]["turn_id"] == "synthetic_turn_01"
        assert rows[0]["field_path"] == "selected_speaker_id"
        assert rows[0]["expected"] == "runner"
        assert rows[0]["actual"] == "guard"
        assert rows[0]["category"] == "speaker"
        assert rows[0]["severity"] == "critical"
        assert rows[0]["primary_owner"] == "speaker"
        assert rows[0]["investigate_first"] == "game/speaker_contract_enforcement.py"

        written = write_protected_replay_failure_report_if_present(
            path=report_path,
            command_used="python -m pytest -m golden_replay -q",
            generated_at="2026-05-26T00:00:00Z",
        )
        assert written == report_path
        report = report_path.read_text(encoding="utf-8")
        assert "# Protected Replay Failure Report" in report
        assert "synthetic_protected_bridge" in report
        assert "selected_speaker_id: exact value mismatch" in report
        assert "## Failure Locator" in report
        assert "| Scenario | Source Path | Branch | Turn Index | Turn ID | Failed Invariant | Test Node |" in report
        assert "data/validation/scenario_spines/synthetic_fixture.json" in report
        assert "synthetic_branch" in report
        assert "synthetic_turn_01" in report
        assert "structural_drift" in report
        assert "game/speaker_contract_enforcement.py" in report
        assert "## Sanitizer Summary" in report
        assert "## Runtime Lineage Summary" in report
        assert "### Focused failing tests" in report
        assert "### Protected replay lane" in report
        assert "python -m pytest -m golden_replay -q --tb=short" in report

        clear_recorded_protected_replay_failures()
        no_identity_turn = {
            key: value
            for key, value in turn.items()
            if key not in {"source_path", "branch_id", "turn_id"}
        }
        with pytest.raises(AssertionError):
            assert_protected_golden_turn_observation(
                no_identity_turn,
                {"equals": {"selected_speaker_id": "runner"}},
                scenario_id="synthetic_inline_bridge",
                debug_context="synthetic inline reporting context",
            )
        no_identity_report_path = tmp_path / "replay_failure_report_no_identity.md"
        written = write_protected_replay_failure_report_if_present(
            path=no_identity_report_path,
            command_used="python -m pytest -m golden_replay -q",
            generated_at="2026-05-26T00:00:00Z",
        )
        assert written == no_identity_report_path
        no_identity_report = no_identity_report_path.read_text(encoding="utf-8")
        assert "synthetic_inline_bridge" in no_identity_report
        assert "## Failure Locator" in no_identity_report
        assert (
            "| synthetic_inline_bridge | none | none | 0 | none | selected_speaker_id: exact value mismatch |"
            in no_identity_report
        )
        assert "python -m pytest -m golden_replay -q --tb=short" in no_identity_report
    finally:
        clear_recorded_protected_replay_failures()


def test_golden_drift_classifier_buckets_exact_structural_and_semantic_drift():
    observed = {
        "final_text": "Planner: the guard shrugs.",
        "route_kind": "action",
        "selected_speaker_id": "guard",
        "final_emitted_source": "global_scene_fallback",
        "fallback_family": "gate_terminal_repair",
        "scaffold_leakage": True,
        "unavailable": [],
        "trace": {"canonical_entry": {"target_actor_id": "guard"}},
    }
    expectation = {
        "exact_text": "The runner answers.",
        "equals": {
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "trace.canonical_entry.target_actor_id": "runner",
        },
        "not_equals": {"final_emitted_source": "global_scene_fallback"},
        "text_must_not_include": ["Planner"],
        "scaffold_leakage": False,
    }

    drift = classify_golden_drift(observed, expectation)

    assert drift["status"] == "fail"
    assert drift["summary"]["exact_drift"] == 1
    assert drift["summary"]["structural_drift"] == 4
    assert drift["summary"]["semantic_drift"] == 2


def test_golden_drift_classification_ignores_runtime_lineage_diagnostics():
    observed = {
        "scenario_id": "lineage_diagnostic_only",
        "turn_index": 0,
        "final_text": "The runner answers.",
        "route_kind": "dialogue",
        "unavailable": [],
    }
    expectation = {"equals": {"route_kind": "dialogue"}}
    baseline = classify_golden_drift(observed, expectation)
    with_lineage = classify_golden_drift(
        {
            **observed,
            "runtime_lineage_events": [
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="scene_opening",
                )
            ],
        },
        expectation,
    )
    assert with_lineage == baseline


def test_golden_drift_opt_in_dashboard_records_lineage_outside_classification_rows(monkeypatch):
    event = make_runtime_lineage_event(
        event_kind="gate_outcome",
        stage="gate",
        owner="game.final_emission_gate",
        gate_path="accept_unchanged",
    )
    clear_recorded_failure_dashboard_rows()
    monkeypatch.setenv("ASHEN_WRITE_FAILURE_DASHBOARD", "1")
    try:
        drift = classify_golden_drift(
            {
                "scenario_id": "recorded_lineage",
                "turn_index": 0,
                "final_text": "The runner answers.",
                "route_kind": "dialogue",
                "unavailable": [],
                "runtime_lineage_events": [event],
            },
            {"equals": {"route_kind": "dialogue"}},
        )
        assert drift["status"] == "pass"
        assert drift["failure_classifications"] == []
        assert recorded_runtime_lineage_events() == [event]
    finally:
        clear_recorded_failure_dashboard_rows()


def _synthetic_rerun_turn(
    *,
    turn_index: int = 0,
    turn_id: str = "t01",
    route_kind: str | None = "dialogue",
    selected_speaker_id: str | None = "runner",
    fallback_family: str | None = None,
    fallback_owner: str | None = None,
    final_text: str = "The runner answers.",
    scaffold_leakage: bool | None = False,
    runtime_lineage_events: list[dict] | None = None,
    response_delta_checked: bool | None = None,
    response_delta_failed: bool | None = None,
    response_delta_repaired: bool | None = None,
    response_delta_kind: str | None = None,
    response_delta_echo_overlap_band: str | None = None,
) -> dict:
    row = {
        "turn_index": turn_index,
        "turn_id": turn_id,
        "route_kind": route_kind,
        "selected_speaker_id": selected_speaker_id,
        "fallback_family": fallback_family,
        "final_text": final_text,
        "runtime_lineage_events": list(runtime_lineage_events or []),
    }
    if fallback_owner is not None:
        row["sealed_fallback_owner_bucket"] = fallback_owner
    if scaffold_leakage is not None:
        row["scaffold_leakage"] = scaffold_leakage
    if response_delta_checked is not None:
        row["response_delta_checked"] = response_delta_checked
    if response_delta_failed is not None:
        row["response_delta_failed"] = response_delta_failed
    if response_delta_repaired is not None:
        row["response_delta_repaired"] = response_delta_repaired
    if response_delta_kind is not None:
        row["response_delta_kind"] = response_delta_kind
    if response_delta_echo_overlap_band is not None:
        row["response_delta_echo_overlap_band"] = response_delta_echo_overlap_band
    return row


def test_compare_golden_replay_reruns_identical_runs_have_zero_deltas():
    turns = [
        _synthetic_rerun_turn(turn_index=0, turn_id="t01"),
        _synthetic_rerun_turn(turn_index=1, turn_id="t02", route_kind="action", selected_speaker_id=None),
    ]

    scorecard = compare_golden_replay_reruns(turns, [dict(turn) for turn in turns])

    assert scorecard["report_only"] is True
    assert scorecard["total_turns_compared"] == 2
    assert scorecard["summary"] == {
        "speaker_delta_count": 0,
        "route_delta_count": 0,
        "fallback_delta_count": 0,
        "text_fingerprint_delta_count": 0,
        "scaffold_delta_count": 0,
        "runtime_lineage_delta_count": 0,
        "semantic_delta_frequency_delta_count": 0,
    }
    assert scorecard["per_turn_deltas"] == []


def test_compare_golden_replay_reruns_counts_speaker_only_drift():
    previous = [_synthetic_rerun_turn(selected_speaker_id="runner")]
    current = [_synthetic_rerun_turn(selected_speaker_id="guard")]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["speaker_delta_count"] == 1
    assert scorecard["summary"]["route_delta_count"] == 0
    assert scorecard["per_turn_deltas"][0]["deltas"]["speaker"] == {
        "previous": "runner",
        "current": "guard",
    }
    assert scorecard["frequencies"]["speakers"]["delta"] == {"guard": 1, "runner": -1}


def test_compare_golden_replay_reruns_counts_route_only_drift():
    previous = [_synthetic_rerun_turn(route_kind="dialogue")]
    current = [_synthetic_rerun_turn(route_kind="action")]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["route_delta_count"] == 1
    assert scorecard["summary"]["speaker_delta_count"] == 0
    assert scorecard["per_turn_deltas"][0]["deltas"]["route"] == {
        "previous": "dialogue",
        "current": "action",
    }
    assert scorecard["frequencies"]["routes"]["delta"] == {"action": 1, "dialogue": -1}


def test_compare_golden_replay_reruns_counts_fallback_frequency_drift():
    event = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind="sealed_or_global_replacement",
        fallback_selection_owner="final_emission_gate",
    )
    previous = [_synthetic_rerun_turn()]
    current = [
        _synthetic_rerun_turn(
            fallback_family="gate_terminal_repair",
            fallback_owner="sealed_gate",
            runtime_lineage_events=[event],
        )
    ]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["fallback_delta_count"] == 1
    assert scorecard["summary"]["runtime_lineage_delta_count"] == 1
    assert scorecard["frequencies"]["fallback_families"]["delta"] == {"gate_terminal_repair": 1}
    assert scorecard["frequencies"]["fallback_owners"]["delta"] == {"sealed_gate": 1}
    assert (
        scorecard["frequencies"]["runtime_lineage"]["frequency_deltas"]["fallback_frequency"]["delta"]
        == {"sealed_or_global_replacement": 1}
    )


def test_compare_golden_replay_reruns_reports_text_fingerprints_without_failing():
    previous = [_synthetic_rerun_turn(final_text="The runner answers.")]
    current = [_synthetic_rerun_turn(final_text="The runner answers with a warning.")]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["text_fingerprint_delta_count"] == 1
    fingerprint_delta = scorecard["per_turn_deltas"][0]["deltas"]["text_fingerprint"]
    assert fingerprint_delta["previous"] != fingerprint_delta["current"]
    assert len(fingerprint_delta["previous"]) == 16
    assert len(fingerprint_delta["current"]) == 16
    assert scorecard["report_only"] is True


def test_compare_golden_replay_reruns_handles_missing_optional_metadata():
    previous = [{"turn_index": 0, "final_text": "Rain falls."}]
    current = [{"turn_index": 0, "final_text": "Rain falls.", "runtime_lineage_events": "not-a-list"}]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["total_turns_compared"] == 1
    assert scorecard["summary"]["speaker_delta_count"] == 0
    assert scorecard["summary"]["route_delta_count"] == 0
    assert scorecard["summary"]["fallback_delta_count"] == 0
    assert scorecard["summary"]["runtime_lineage_delta_count"] == 0
    assert scorecard["summary"]["semantic_delta_frequency_delta_count"] == 0
    assert scorecard["frequencies"]["response_delta"]["previous"]["response_delta_unknown_count"] == 1
    assert scorecard["frequencies"]["response_delta"]["current"]["response_delta_unknown_count"] == 1
    assert scorecard["per_turn_deltas"] == []


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


def test_long_session_summary_counts_response_delta_metadata():
    turns = [
        _synthetic_rerun_turn(
            response_delta_checked=True,
            response_delta_failed=False,
            response_delta_repaired=False,
            response_delta_kind="new_fact",
            response_delta_echo_overlap_band="low",
        ),
        _synthetic_rerun_turn(
            turn_index=1,
            response_delta_checked=True,
            response_delta_failed=True,
            response_delta_repaired=True,
            response_delta_kind="new_fact",
            response_delta_echo_overlap_band="high",
        ),
        _synthetic_rerun_turn(turn_index=2),
    ]

    summary = summarize_long_session_replay_observations(turns)["response_delta_summary"]

    assert summary["response_delta_checked_count"] == 2
    assert summary["response_delta_failed_count"] == 1
    assert summary["response_delta_repaired_count"] == 1
    assert summary["response_delta_kind_counts"] == {"new_fact": 2}
    assert summary["response_delta_unknown_count"] == 1
    assert summary["echo_overlap_band_counts"] == {"high": 1, "low": 1}


def test_compare_golden_replay_reruns_reports_response_delta_frequency_deltas():
    previous = [
        _synthetic_rerun_turn(
            response_delta_checked=True,
            response_delta_failed=False,
            response_delta_repaired=False,
            response_delta_kind="new_fact",
            response_delta_echo_overlap_band="low",
        )
    ]
    current = [
        _synthetic_rerun_turn(
            response_delta_checked=True,
            response_delta_failed=True,
            response_delta_repaired=True,
            response_delta_kind="new_actionable_lead",
            response_delta_echo_overlap_band="high",
        )
    ]

    scorecard = compare_golden_replay_reruns(previous, current)

    assert scorecard["summary"]["semantic_delta_frequency_delta_count"] == 1
    response_delta = scorecard["frequencies"]["response_delta"]
    assert response_delta["failed"]["delta"] == {"failed": 1}
    assert response_delta["repaired"]["delta"] == {"repaired": 1}
    assert response_delta["kinds"]["delta"] == {"new_actionable_lead": 1, "new_fact": -1}
    assert response_delta["echo_overlap_bands"]["delta"] == {"high": 1, "low": -1}
    assert scorecard["per_turn_deltas"][0]["deltas"]["response_delta"]["response_delta_failed"] == {
        "previous": False,
        "current": True,
    }


def _synthetic_rerun_scorecard() -> dict:
    event = make_runtime_lineage_event(
        event_kind="fallback_selected",
        stage="gate",
        owner="game.final_emission_gate",
        fallback_kind="sealed_or_global_replacement",
    )
    return compare_golden_replay_reruns(
        [_synthetic_rerun_turn(final_text="The runner answers.")],
        [
            _synthetic_rerun_turn(
                selected_speaker_id="guard",
                route_kind="action",
                fallback_family="gate_terminal_repair",
                fallback_owner="sealed_gate",
                final_text="The guard answers.",
                runtime_lineage_events=[event],
            )
        ],
    )


def test_rerun_drift_scorecard_markdown_summarizes_fabricated_scorecard():
    scorecard = _synthetic_rerun_scorecard()

    markdown = render_rerun_drift_scorecard_markdown(
        scorecard,
        generated_at="2026-05-30T00:00:00Z",
        command_used="pytest synthetic",
    )

    assert "# Golden Rerun Drift Scorecard" in markdown
    assert "- Total turns compared: `1`" in markdown
    assert "- Speaker deltas: `1`" in markdown
    assert "- Route deltas: `1`" in markdown
    assert "- Fallback deltas: `1`" in markdown
    assert "- Text fingerprint deltas: `1`" in markdown
    assert "- Runtime-lineage deltas: `1`" in markdown
    assert "## Semantic Delta Frequency" in markdown
    assert "- Semantic delta frequency deltas: `0`" in markdown
    assert "| Turn | Previous Turn ID | Current Turn ID | Drift Fields | Details |" in markdown
    assert "text_hash" in markdown


def test_rerun_drift_scorecard_writer_creates_json_and_markdown(tmp_path):
    scorecard = _synthetic_rerun_scorecard()
    json_path = tmp_path / "rerun_drift_scorecard.json"
    markdown_path = tmp_path / "rerun_drift_scorecard.md"

    written_json, written_markdown = write_rerun_drift_scorecard_artifacts(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-05-30T00:00:00Z",
        command_used="pytest synthetic",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    assert json.loads(json_path.read_text(encoding="utf-8")) == scorecard
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Golden Rerun Drift Scorecard" in markdown
    assert "Speaker deltas: `1`" in markdown


def test_rerun_drift_scorecard_writer_is_opt_in_by_default(tmp_path):
    scorecard = _synthetic_rerun_scorecard()
    json_path = tmp_path / "default_off.json"
    markdown_path = tmp_path / "default_off.md"

    written = write_rerun_drift_scorecard_artifacts_if_requested(
        scorecard,
        json_path=json_path,
        markdown_path=markdown_path,
        env={},
    )

    assert written is None
    assert not json_path.exists()
    assert not markdown_path.exists()


def test_rerun_drift_scorecard_writer_handles_missing_comparison(tmp_path):
    json_path = tmp_path / "no_comparison.json"
    markdown_path = tmp_path / "no_comparison.md"

    written_json, written_markdown = write_rerun_drift_scorecard_artifacts(
        None,
        json_path=json_path,
        markdown_path=markdown_path,
        generated_at="2026-05-30T00:00:00Z",
        command_used="pytest synthetic",
    )

    assert written_json == json_path
    assert written_markdown == markdown_path
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["comparison_available"] is False
    assert "No rerun comparison available" in markdown_path.read_text(encoding="utf-8")


def test_rerun_drift_scorecard_recording_does_not_change_failure_dashboard_behavior(tmp_path):
    scorecard = _synthetic_rerun_scorecard()
    clear_recorded_rerun_drift_scorecards()
    clear_recorded_protected_replay_failures()
    try:
        record_rerun_drift_scorecard(scorecard)

        assert recorded_rerun_drift_scorecards() == [scorecard]
        assert write_protected_replay_failure_report_if_present(path=tmp_path / "failure_report.md") is None
    finally:
        clear_recorded_rerun_drift_scorecards()
        clear_recorded_protected_replay_failures()


def test_golden_markdown_report_renderer_is_compact_and_deterministic():
    rows = [
        {
            "scenario_id": "zeta",
            "mode": "end-to-end",
            "turn_count": 1,
            "status": "pass",
            "drift": {"status": "pass", "summary": {"exact_drift": 0, "structural_drift": 0, "semantic_drift": 0}},
            "final_emitted_source": ["generated_candidate"],
            "fallback_family": [],
            "unavailable_fields": ["fallback_family"],
            "required_invariants": ["speaker lock"],
        },
        {
            "scenario_id": "alpha",
            "mode": "schema-smoke",
            "turn_count": 3,
            "status": "pass",
            "drift_summary": "exact=0, structural=0, semantic=0",
            "final_emitted_source": ["retry_output"],
            "fallback_family": ["none"],
            "unavailable_fields": [],
            "required_invariants": ["branch ids"],
        },
    ]

    report = render_golden_replay_markdown_report(rows, title="Synthetic Report")

    assert report.index("| alpha |") < report.index("| zeta |")
    assert "Exact prose comparison is opt-in" in report
    assert "| Scenario | Mode | Turns | Status | Drift | Classifications |" in report


def test_long_session_replay_summary_renderer_surfaces_operator_metrics():
    turns = [
        {
            "turn_index": 0,
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "post_gate_mutation_detected": False,
            "unavailable": [],
            "runtime_lineage_events": [],
        },
        {
            "turn_index": 1,
            "route_kind": "dialogue",
            "selected_speaker_id": "runner",
            "post_gate_mutation_detected": True,
            "unavailable": ["fallback_family"],
            "runtime_lineage_events": [
                {
                    "event_type": "runtime_lineage",
                    "event_kind": "fallback_selected",
                    "stage": "gate",
                    "owner": "game.final_emission_gate",
                    "source": "neutral_reply_speaker_grounding_bridge",
                    "fallback_kind": "sealed_or_global_replacement",
                    "recurrence_key": "fallback_selected:gate:game.final_emission_gate:sealed_or_global_replacement",
                }
            ],
        },
    ]
    summary = {
        "turn_count": 2,
        "route_frequency": {"dialogue": 2},
        "route_change_count": 0,
        "speaker_frequency": {"runner": 2},
        "speaker_change_count": 0,
        "speaker_missing_count": 0,
        "mutation_turn_count": 1,
        "unavailable_counts": {"fallback_family": 1},
        "response_delta_summary": {
            "response_delta_checked_count": 1,
            "response_delta_failed_count": 0,
            "response_delta_repaired_count": 0,
            "response_delta_kind_counts": {"new_fact": 1},
            "response_delta_unknown_count": 1,
            "echo_overlap_band_counts": {"low": 1},
        },
        "lineage_summary": {
            "by_event_kind": {"fallback_selected": 1},
            "recurring_events": [
                {
                    "recurrence_key": "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
                    "count": 2,
                }
            ],
        },
        "fallback_escalation_summary": {
            "fallback_total_count": 1,
            "fallback_family_counts": {},
            "fallback_owner_counts": {},
            "fallback_lineage_kind_counts": {"sealed_or_global_replacement": 1},
            "max_fallback_streak": 1,
            "late_window_fallback_count": 0,
            "escalation_warnings": [],
        },
        "continuity_warning_count": 0,
        "continuity_violation_count": 0,
        "continuity_drift": {
            "session_health": {"classification": "clean", "degradation_detected": False},
            "degradation_over_time": {"reason_codes": [], "late_window": {"signals": []}},
        },
    }

    report = render_long_session_replay_summary_markdown(
        scenario_id="synthetic_long_session",
        turns=turns,
        summary=summary,
        title="Synthetic Long Session",
    )

    assert "- Route changes: `0`" in report
    assert "- Speaker changes / missing: `0` / `0`" in report
    assert "- Continuity classification: `clean`" in report
    assert "- Fallback total count: `1`" in report
    assert "- Fallback lineage kinds: `{'sealed_or_global_replacement': 1}`" in report
    assert "- Mutation turn count: `1`" in report
    assert "- Response-delta checked / failed / repaired: `1` / `0` / `0`" in report
    assert "- Response-delta kinds: `{'new_fact': 1}`" in report
    assert "- Response-delta unknown count: `1`" in report
    assert "- Echo-overlap bands: `{'low': 1}`" in report
    assert "- Unavailable counts: `{'fallback_family': 1}`" in report
    assert "- Lineage recurrence: `[" in report
    assert "- Fallback frequency:" not in report
    assert "- Mutation turns:" not in report


# Opening fallback projection fields are repeated here as replay contract locks;
# the owner-bucket mapper itself is owned by tests/test_opening_fallback_owner_bucket.py.
def test_golden_observed_turn_projects_canonical_upstream_prepared_opening_owner_bucket():
    observed = project_synthetic_turn(
        scenario_id="synthetic_opening_owner",
        gm_text="The road opens.",
        fem_meta=successful_opening_fem_meta(
            response_type_repair_kind="opening_deterministic_fallback",
            fallback_temporal_frame="first_impression",
        ),
    )

    assert observed["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


def test_golden_observed_turn_projects_runtime_lineage_and_prefers_existing_events():
    existing = make_runtime_lineage_event(
        event_kind="speaker_repair",
        stage="gate",
        owner="game.speaker_contract_enforcement",
        source="provided_projection",
        repair_kind="local_rebind",
    )
    observed = project_synthetic_turn(
        scenario_id="existing_lineage_projection",
        gm_text="The road opens.",
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="opening_deterministic_fallback",
                opening_recovered_via_fallback=True,
                fallback_family_used="scene_opening",
            ),
            metadata={"observability_bundle": {"fem_runtime_lineage_events": [existing]}},
        ),
    )
    assert observed["runtime_lineage_events"] == [existing]

    from_fem = project_synthetic_turn(
        scenario_id="fem_lineage_projection",
        gm_text="The road opens.",
        fem_meta=successful_opening_fem_meta(),
    )
    opening_selected = next(
        event for event in from_fem["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    assert opening_selected["fallback_kind"] == "scene_opening"
    assert opening_selected["owner"] == "game.final_emission_gate"
    assert opening_selected["fallback_selection_owner"] == "game.final_emission_gate"
    assert opening_selected["fallback_content_owner"] == "game.opening_deterministic_fallback"
    assert opening_selected["fallback_authorship_source"] == "upstream_prepared_opening_fallback"
    assert opening_selected["fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    debug = format_golden_replay_debug(
        {"scenario_id": from_fem["scenario_id"], "turn_count": 1, "turns": [from_fem]}
    )
    assert "'fallback_authorship_source': 'upstream_prepared_opening_fallback'" in debug
    assert "'fallback_owner_bucket': 'upstream-prepared'" in debug

    missing = project_synthetic_turn(
        scenario_id="missing_lineage_projection",
        gm_text="The road remains quiet.",
        payload=minimal_gm_output_payload(player_facing_text="The road remains quiet."),
    )
    assert missing["runtime_lineage_events"] == []


def test_golden_observed_turn_projects_neutral_speaker_grounding_replacement_family():
    observed = project_synthetic_turn(
        scenario_id="neutral_grounding_family_projection",
        gm_text="The moment passes without anyone stepping forward to own that thread.",
        player_text="I force the side door.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source=NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            response_type_repair_used=False,
        ),
    )

    assert observed["fallback_family"] == NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY
    assert "fallback_family" not in observed["unavailable"]
    fallback_selected = [
        event
        for event in observed["runtime_lineage_events"]
        if event.get("event_kind") == "fallback_selected"
    ]
    assert fallback_selected[0]["fallback_kind"] == "sealed_unknown_replacement"

    summary = summarize_long_session_replay_observations([observed])
    fallback_escalation = summary["fallback_escalation_summary"]
    assert summary["fallback_turn_count"] == 1
    assert fallback_escalation["fallback_selected_without_family_count"] == 0
    assert "fallback_selected_without_family_recurrence" not in fallback_escalation["escalation_warnings"]


def test_long_session_summary_treats_scene_action_fallback_speaker_absence_as_optional():
    turns = [
        {
            "turn_index": 0,
            "route_kind": "undecided",
            "response_type_required": "neutral_narration",
            "final_emitted_source": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            "fallback_family": NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
            "unavailable": ["selected_speaker_id"],
            "runtime_lineage_events": [
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="sealed_or_global_replacement",
                )
            ],
        },
        {
            "turn_index": 1,
            "route_kind": "action",
            "response_type_required": "action_outcome",
            "final_emitted_source": "anti_reset_local_continuation_fallback",
            "fallback_family": "gate_terminal_repair",
            "unavailable": ["selected_speaker_id"],
            "runtime_lineage_events": [
                make_runtime_lineage_event(
                    event_kind="fallback_selected",
                    stage="gate",
                    owner="game.final_emission_gate",
                    fallback_kind="response_type_prepared_emission",
                )
            ],
        },
    ]

    fallback_escalation = summarize_long_session_replay_observations(turns)["fallback_escalation_summary"]

    assert fallback_escalation["unavailable_with_fallback_count"] == 2
    assert fallback_escalation["scene_action_speaker_optional_unavailable_count"] == 2
    assert fallback_escalation["blocking_unavailable_with_fallback_count"] == 0
    assert fallback_escalation["max_fallback_streak"] == 2
    assert fallback_escalation["max_scene_action_nonblocking_fallback_streak"] == 2
    assert fallback_escalation["max_blocking_fallback_streak"] == 0
    assert "fallback_streak_gt_1" not in fallback_escalation["escalation_warnings"]
    assert "unavailable_to_fallback_coupling_recurrence" not in fallback_escalation["escalation_warnings"]


def test_golden_observed_turn_projects_fail_closed_sealed_gate_opening_owner_bucket():
    observed = project_synthetic_turn(
        scenario_id="synthetic_opening_owner_fail_closed",
        gm_text="[opening_fallback_failed_closed:no_curated_facts]",
        fem_meta=fail_closed_opening_fem_meta(
            opening_recovered_via_fallback=True,
            fallback_family_used="scene_opening",
        ),
    )

    assert observed["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_SEALED_GATE
    failed_closed_selected = next(
        event for event in observed["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    assert failed_closed_selected["fallback_kind"] == "opening_failed_closed"
    assert failed_closed_selected["fallback_selection_owner"] == "game.final_emission_gate"
    assert failed_closed_selected["fallback_content_owner"] == "game.final_emission_gate"
    assert failed_closed_selected["fallback_authorship_source"] is None
    assert failed_closed_selected["fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_SEALED_GATE
    debug = format_golden_replay_debug(
        {"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]}
    )
    assert "'fallback_kind': 'opening_failed_closed'" in debug
    assert "'fallback_owner_bucket': 'sealed-gate'" in debug


# Sealed fallback projection fields are replay contract locks. Helper shaping is
# owned by final_emission_sealed_fallback; gate branch selection/output remains
# owned by final_emission_gate.
def test_golden_observed_turn_projects_sealed_fallback_owner_bucket():
    observed = project_synthetic_turn(
        scenario_id="synthetic_sealed_owner",
        gm_text="A sealed fallback line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
            realization_fallback_family="gate_terminal_repair",
        ),
    )

    assert observed["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_SEALED_GATE


def test_golden_observed_turn_projects_strict_social_sealed_fallback_owner_bucket():
    observed = project_synthetic_turn(
        scenario_id="synthetic_strict_social_sealed_owner",
        gm_text="A strict-social sealed fallback line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="minimal_social_emergency_fallback",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
            realization_fallback_family="strict_social_deterministic_fallback",
        ),
    )

    assert observed["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED
    fallback_selected = next(
        event for event in observed["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    assert fallback_selected["fallback_kind"] == "minimal_social_emergency_fallback"
    assert fallback_selected["owner"] == "game.final_emission_gate"
    assert fallback_selected["fallback_selection_owner"] == "game.final_emission_gate"
    assert fallback_selected["fallback_content_owner"] == "game.social_exchange_emission"


def test_golden_observed_turn_projects_visibility_fallback_evidence():
    observed = project_synthetic_turn(
        scenario_id="synthetic_visibility_owner",
        gm_text="A visibility fallback line.",
        fem_meta=fem_payload(
            final_route="replaced",
            final_emitted_source="global_scene_fallback",
            visibility_fallback_owner_bucket="sealed-gate",
            visibility_replacement_applied=True,
            visibility_fallback_pool="global_scene_narrative",
            visibility_fallback_kind="narrative_safe_fallback",
            sealed_fallback_owner_bucket=SEALED_FALLBACK_OWNER_SEALED_GATE,
        ),
    )

    assert observed["visibility_fallback_owner_bucket"] == "sealed-gate"
    assert observed["visibility_replacement_applied"] is True
    assert observed["visibility_fallback_pool"] == "global_scene_narrative"
    assert observed["visibility_fallback_kind"] == "narrative_safe_fallback"
    fallback_selected = next(
        event for event in observed["runtime_lineage_events"] if event["event_kind"] == "fallback_selected"
    )
    gate_outcome = next(
        event for event in observed["runtime_lineage_events"] if event["event_kind"] == "gate_outcome"
    )
    assert fallback_selected["fallback_kind"] == "visibility_or_scene_replacement"
    assert gate_outcome["gate_path"] == "visibility_or_scene_replaced"


@pytest.mark.parametrize(
    ("required", "repair_kind", "source"),
    [
        (
            "answer",
            "answer_upstream_prepared_repair",
            "upstream_prepared_emission.prepared_answer_fallback_text",
        ),
        (
            "action_outcome",
            "action_outcome_upstream_prepared_repair",
            "upstream_prepared_emission.prepared_action_fallback_text",
        ),
    ],
)
def test_golden_observed_turn_projects_valid_upstream_prepared_emission_telemetry(required, repair_kind, source):
    observed = project_synthetic_turn(
        scenario_id=f"{required}_prepared_projection",
        gm_text="Projected prepared text.",
        player_text="Do the thing.",
        resolution={"kind": "investigate"},
        fem_meta=fem_payload(
            final_emitted_source=repair_kind,
            response_type_required=required,
            response_type_candidate_ok=True,
            response_type_repair_used=True,
            response_type_repair_kind=repair_kind,
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=True,
            upstream_prepared_emission_source=source,
            upstream_prepared_emission_reject_reason=None,
            realization_fallback_family="upstream_prepared_emission",
        ),
    )

    assert observed["upstream_prepared_emission_used"] is True
    assert observed["upstream_prepared_emission_valid"] is True
    assert observed["upstream_prepared_emission_source"] == source
    assert observed["upstream_prepared_emission_reject_reason"] is None
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert f"upstream_prepared_emission_source: {source!r}" in debug


def test_golden_observed_turn_projects_rejected_upstream_prepared_emission_telemetry():
    observed = project_synthetic_turn(
        scenario_id="rejected_prepared_projection",
        gm_text="You pry the chest, but nothing gives yet.",
        player_text="Pry the chest.",
        resolution={"kind": "investigate"},
        fem_meta=fem_payload(
            final_emitted_source="generated_candidate",
            response_type_required="action_outcome",
            response_type_candidate_ok=False,
            response_type_repair_used=False,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source="upstream_prepared_emission.prepared_action_fallback_text",
            upstream_prepared_emission_reject_reason="action_outcome_replaced_by_dialogue",
            realization_fallback_family="upstream_prepared_emission",
        ),
    )

    assert observed["upstream_prepared_emission_used"] is False
    assert observed["upstream_prepared_emission_valid"] is False
    assert observed["upstream_prepared_emission_source"] == "upstream_prepared_emission.prepared_action_fallback_text"
    assert observed["upstream_prepared_emission_reject_reason"] == "action_outcome_replaced_by_dialogue"
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "upstream_prepared_emission_reject_reason: 'action_outcome_replaced_by_dialogue'" in debug


@pytest.mark.parametrize(
    ("required", "repair_kind", "source"),
    [
        ("answer", None, "absent"),
        ("action_outcome", None, "absent"),
    ],
)
def test_golden_observed_turn_projects_absent_upstream_prepared_emission_telemetry(required, repair_kind, source):
    observed = project_synthetic_turn(
        scenario_id=f"{required}_prepared_absent_projection",
        gm_text="Only mist between the torches.",
        player_text="Can I do it?",
        resolution={"kind": "investigate"},
        fem_meta=fem_payload(
            final_emitted_source="generated_candidate",
            response_type_required=required,
            response_type_candidate_ok=False,
            response_type_repair_used=False,
            response_type_repair_kind=repair_kind,
            response_type_upstream_prepared_absent=True,
            upstream_prepared_emission_used=False,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source=source,
            upstream_prepared_emission_reject_reason=None,
        ),
    )

    assert observed["upstream_prepared_emission_used"] is False
    assert observed["upstream_prepared_emission_valid"] is False
    assert observed["upstream_prepared_emission_source"] == "absent"
    assert observed["upstream_prepared_emission_reject_reason"] is None
    assert observed["raw_signal_presence"]["upstream_prepared_emission_used"] is True
    assert observed["raw_signal_presence"]["upstream_prepared_emission_valid"] is True
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "upstream_prepared_emission_used: False" in debug
    assert "upstream_prepared_emission_source: 'absent'" in debug


def test_golden_drift_classification_preserves_malformed_prepared_emission_reject_reason():
    observed = project_synthetic_turn(
        scenario_id="malformed_prepared_projection",
        gm_text="The lock remains stubborn.",
        player_text="Pry the lock.",
        resolution={"kind": "investigate"},
        fem_meta=fem_payload(
            final_emitted_source="generated_candidate",
            response_type_required="action_outcome",
            response_type_candidate_ok=False,
            response_type_repair_used=False,
            response_type_repair_kind="action_outcome_upstream_prepared_repair",
            upstream_prepared_emission_used=True,
            upstream_prepared_emission_valid=False,
            upstream_prepared_emission_source="upstream_prepared_emission.prepared_action_fallback_text",
            upstream_prepared_emission_reject_reason="action_outcome_missing_result",
            realization_fallback_family="upstream_prepared_emission",
        ),
    )

    drift = classify_golden_drift(
        observed,
        {
            "equals": {
                "upstream_prepared_emission_valid": True,
            }
        },
    )

    assert observed["upstream_prepared_emission_used"] is True
    assert observed["upstream_prepared_emission_valid"] is False
    assert observed["upstream_prepared_emission_reject_reason"] == "action_outcome_missing_result"
    row = drift["failure_classifications"][0]
    assert row["primary_owner"] == "upstream_prepared_emission"
    assert row["upstream_prepared_emission_reject_reason"] == "action_outcome_missing_result"
    debug = format_golden_replay_debug(
        {"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed], "drift": drift}
    )
    assert "upstream_prepared_emission_reject_reason: 'action_outcome_missing_result'" in debug
    assert "owner='upstream_prepared_emission'" in debug


def test_golden_observed_turn_projects_sanitizer_empty_fallback_as_sanitizer_owned():
    observed = project_synthetic_turn(
        scenario_id="sanitizer_empty_projection",
        gm_text="For a breath, the scene stays still.",
        player_text="Wait.",
        resolution={"kind": "observe"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="generated_candidate",
                final_emission_mutation_lineage=[
                    "pre_gate_sanitizer",
                    "sanitizer_empty_fallback",
                    "finalize_packaging",
                ],
                response_type_repair_used=False,
                upstream_prepared_emission_used=False,
                upstream_prepared_emission_valid=False,
                upstream_prepared_emission_source=None,
                upstream_prepared_emission_reject_reason=None,
            ),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_boundary_mode": "strip_only",
                    "sanitizer_empty_fallback_used": True,
                    "sanitizer_empty_fallback_source": "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text",
                    "sanitizer_empty_fallback_owner": "output_sanitizer",
                }
            },
        ),
    )

    assert observed["sanitizer_empty_fallback_used"] is True
    assert observed["sanitizer_empty_fallback_source"] == "upstream_prepared_emission.prepared_sanitizer_empty_fallback_text"
    assert observed["sanitizer_empty_fallback_owner"] == "output_sanitizer"
    assert observed["upstream_prepared_emission_used"] is False
    assert observed["sanitizer_lineage_mode"] == "strip_only"
    assert observed["sanitizer_lineage_empty_fallback_used"] is True
    assert "sanitizer_empty_fallback" in observed["final_emission_mutation_lineage"]
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "sanitizer_empty_fallback_owner: 'output_sanitizer'" in debug
    assert "sanitizer_lineage_empty_fallback_used: True" in debug
    assert "final_emission_mutation_lineage" in debug


def test_golden_observed_turn_projects_strict_social_sanitizer_fallback_owner_split():
    observed = project_synthetic_turn(
        scenario_id="strict_social_sanitizer_split",
        gm_text='The runner says, "No names."',
        player_text="Ask the runner.",
        resolution={"kind": "question"},
        payload=minimal_gm_output_payload(
            fem_meta=fem_payload(
                final_emitted_source="generated_candidate",
                strict_social_active=True,
                upstream_prepared_emission_used=False,
                upstream_prepared_emission_valid=False,
                upstream_prepared_emission_source=None,
                upstream_prepared_emission_reject_reason=None,
            ),
            metadata={
                "sanitizer_trace": {
                    "sanitizer_lineage_mode": "strip_only",
                    "sanitizer_strict_social_fallback_used": True,
                    "sanitizer_strict_social_selection_owner": "output_sanitizer",
                    "sanitizer_strict_social_prose_owner": "strict_social_emission",
                    "sanitizer_strict_social_source": "social_fallback_line_for_sanitizer.empty_output",
                }
            },
        ),
    )

    assert observed["sanitizer_strict_social_fallback_used"] is True
    assert observed["sanitizer_strict_social_selection_owner"] == "output_sanitizer"
    assert observed["sanitizer_strict_social_prose_owner"] == "strict_social_emission"
    assert observed["sanitizer_strict_social_source"] == "social_fallback_line_for_sanitizer.empty_output"
    assert observed["sanitizer_empty_fallback_used"] is None
    assert observed["upstream_prepared_emission_used"] is False
    debug = format_golden_replay_debug({"scenario_id": observed["scenario_id"], "turn_count": 1, "turns": [observed]})
    assert "sanitizer_strict_social_selection_owner: 'output_sanitizer'" in debug
    assert "sanitizer_strict_social_prose_owner: 'strict_social_emission'" in debug


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


def test_golden_replay_directed_npc_question_structural_invariants(tmp_path, monkeypatch):
    captured_prompts: list[list[dict]] = []

    def _fake_call_gpt(messages):
        captured_prompts.append(messages)
        return gm_response('Tavern Runner grimaces. "I heard east-road talk, but no names."')

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="directed_npc_question",
        turns=["Runner, who attacked the patrol?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_investigator_runner_world,
    )

    assert captured_prompts
    assert result["turn_count"] == 1
    turn = result["turns"][0]
    directed_npc_question_expectation = protected_social_structural_base(
        selected_speaker_id="runner",
        canonical_target_id="runner",
        require_resolution_kind=True,
        require_final_emitted_source=True,
        require_trace_target=True,
        require_trace_route=True,
        include_resolution_kind=True,
        include_trace_route=True,
        disallow_global_scene_fallback=True,
    )
    assert_protected_golden_turn_observation(
        turn,
        directed_npc_question_expectation,
        scenario_id="directed_npc_question",
        debug_context=format_golden_replay_debug(result),
    )


def test_golden_replay_vocative_override_after_prior_continuity_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            gm_response('Tavern Runner says, "I saw the patrol turn toward the east lanes."'),
            gm_response('Gate Guard says, "I saw fresh mud by the north arch."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="vocative_override_after_prior_continuity",
        turns=[
            "Runner, where did the patrol go?",
            "Guard, what did you see?",
        ],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_runner_guard_world,
    )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="guard",
            require_route_kind=False,
            require_final_emitted_source=False,
            allow_unavailable=(
                "fallback_family",
                "final_emitted_source",
                "route_kind",
                "trace.canonical_entry",
                "trace.turn_trace",
                "trace.social_contract_trace",
            ),
            include_route_kind=False,
        ),
        scenario_id="vocative_override_after_prior_continuity",
        debug_context=debug_context,
    )
    if "route_kind" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            {
                **protected_unavailable_expectation("fallback_family"),
                **protected_route_expectation(),
            },
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_protected_golden_turn_observation(
            turn,
            {
                **protected_unavailable_expectation("fallback_family"),
                "equals": {"trace.canonical_entry.target_actor_id": "guard"},
                "one_of": {
                    "trace.canonical_entry.target_source": ["spoken_vocative", "vocative"],
                    "trace.canonical_entry.reason": [
                        "spoken_vocative_address",
                        "spoken_vocative_resolved_to_addressable_actor",
                        "explicit_spoken_vocative_overrode_continuity",
                        "spoken_vocative_overrode_continuity",
                    ],
                },
            },
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )
    social_contract_trace = (turn.get("trace") or {}).get("social_contract_trace") or {}
    if social_contract_trace.get("route_selected") is not None:
        assert_protected_golden_turn_observation(
            turn,
            {
                **protected_unavailable_expectation("fallback_family"),
                **protected_route_expectation(include_route_kind=False, include_trace_route=True),
            },
            scenario_id="vocative_override_after_prior_continuity",
            debug_context=debug_context,
        )


def test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response('Merchant says, "I know nothing about that."'),
    )

    result = run_golden_replay(
        scenario_id="wrong_speaker_strict_social_emission",
        turns=["Who attacked the patrol?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_runner_continuity_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="runner",
            allow_unavailable=("fallback_family", "final_emitted_source"),
            require_route_kind=False,
            require_final_emitted_source=False,
            include_route_kind=False,
            extra_no_scaffold_terms=("Merchant",),
        ),
        scenario_id="wrong_speaker_strict_social_emission",
        debug_context=debug_context,
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            {
                **protected_unavailable_expectation("fallback_family"),
                "require_present": ["final_emitted_source"],
            },
            scenario_id="wrong_speaker_strict_social_emission",
            debug_context=debug_context,
        )


def test_golden_direct_seam_declared_alias_dialogue_plan_structural_invariants(monkeypatch):
    session, world, scene_id, resolution = runner_strict_bundle()
    attach_dialogue_social_plan_to_resolution(
        resolution,
        make_valid_dialogue_social_plan(
            speaker_id="tavern_runner",
            speaker_name="Tavern Runner",
            dialogue_intent="question",
            allowed_pregate_speaker_labels=["Ragged stranger"],
            speaker_alias_resolution_source="manual_bundle_override",
        ),
    )
    patch_get_speaker_selection_contract(monkeypatch, locked_runner_contract())
    pre_gate_line = 'Ragged stranger says, "No names, only rumors."'
    patch_build_final_strict_social_response(
        monkeypatch, line=pre_gate_line, strict_social_details=stub_strict_social_details
    )

    out = apply_final_emission_gate(
        {"player_facing_text": pre_gate_line, "tags": []},
        resolution=resolution,
        session=session,
        scene_id=scene_id,
        world=world,
    )

    final_text = str(out.get("player_facing_text") or "")
    meta = read_fem_meta_from_gate_output(out) or {}
    npc_id = (resolution.get("social") or {}).get("npc_id")
    turn = observed_turn_from_gate_output(
        scenario_id="declared_alias_dialogue_plan",
        gm_output=out,
        resolution=resolution,
        extra_fields={
            "trace": {
                "canonical_entry": {
                    "target_actor_id": npc_id,
                    "declared_alias_target_actor_id": npc_id,
                    "allowed_pregate_speaker_labels": ["Ragged stranger"],
                    "speaker_alias_resolution_source": "manual_bundle_override",
                }
            },
            "dialogue_plan_valid": meta.get("dialogue_plan_valid"),
        },
        unavailable=["fallback_family"],
    )

    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="runner",
            canonical_target_id="runner",
            require_present=("trace.canonical_entry.declared_alias_target_actor_id",),
            require_route_kind=False,
            equals={
                "trace.canonical_entry.declared_alias_target_actor_id": "runner",
                "trace.canonical_entry.speaker_alias_resolution_source": "manual_bundle_override",
                "dialogue_plan_valid": True,
            },
            include_route_kind=False,
        ),
        scenario_id="declared_alias_dialogue_plan",
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )


def test_golden_replay_thin_answer_action_outcome_final_emission_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response("The scene pauses without offering anything concrete."),
        suppress_exploration=False,
        suppress_intent=False,
    )

    result = run_golden_replay(
        scenario_id="thin_answer_action_outcome_final_emission",
        turns=["I examine the notice board; does it show where the missing patrol went?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_scene_object_investigation_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    low = str(turn.get("final_text") or "").lower()
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=("final_text", "final_emitted_source"),
            allow_unavailable=(
                "fallback_family",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ),
            equals={
                "response_type_required": "action_outcome",
                "response_type_repair_used": True,
            },
            include_route_kind=False,
            disallow_global_scene_fallback=True,
            extra_no_scaffold_terms=(
                "scene pauses",
                "nothing concrete",
                "no name comes clear",
            ),
        ),
        scenario_id="thin_answer_action_outcome_final_emission",
        debug_context=debug_context,
    )
    assert "patrol" in low or "east ridge" in low or "notice" in low, debug_context
    assert turn.get("sanitizer_lineage_legacy_rewrite_active") is not True


def test_golden_replay_sanitizer_scaffold_leakage_structural_invariants(tmp_path, monkeypatch):
    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=lambda _messages: gm_response(
            "Planner: route via router. Validator: unresolved scaffold."
        ),
    )

    result = run_golden_replay(
        scenario_id="sanitizer_scaffold_leakage",
        turns=["Where should I start?"],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_scene_object_investigation_world,
    )

    assert result["turn_count"] == 1
    turn = result["turns"][0]
    assert turn.get("sanitizer_lineage_legacy_rewrite_active") is not True
    assert_protected_golden_turn_observation(
        turn,
        protected_structural_expectation(
            require_present=("final_text",),
            allow_unavailable=(
                "fallback_family",
                "final_emitted_source",
                "selected_speaker_id",
                "trace.canonical_entry",
                "trace.social_contract_trace",
            ),
            include_route_kind=False,
            extra_no_scaffold_terms=("Planner", "Validator"),
        ),
        scenario_id="sanitizer_scaffold_leakage",
        debug_context=format_golden_replay_debug(result),
    )
    if "final_emitted_source" not in turn.get("unavailable", []):
        assert_protected_golden_turn_observation(
            turn,
            {
                **protected_unavailable_expectation(
                    "fallback_family",
                    "selected_speaker_id",
                    "trace.canonical_entry",
                    "trace.social_contract_trace",
                ),
                "require_present": ["final_emitted_source"],
            },
            scenario_id="sanitizer_scaffold_leakage",
            debug_context=format_golden_replay_debug(result),
        )


def test_golden_direct_seam_canonical_opening_fallback_path_has_no_compatibility_local_ownership():
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    final_text = str(out.get("player_facing_text") or "")
    meta = read_fem_meta_from_gate_output(out) or {}
    turn = observed_turn_from_gate_output(
        scenario_id="opening_fallback_path",
        gm_output=out,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        unavailable=[],
    )

    assert_protected_golden_turn_observation(
        turn,
        {
            "require_present": ["final_text", "final_emitted_source", "fallback_family", "opening_fallback_owner_bucket"],
            "equals": successful_opening_observed_fields(
                include_owner_bucket=True,
                response_type_required="scene_opening",
                response_type_repair_used=True,
            ),
            "not_equals": {
                "opening_fallback_authorship_source": OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL,
            },
            **protected_no_scaffold_expectation(),
        },
        scenario_id="opening_fallback_path",
        debug_context=f"meta={meta!r}; final_text={final_text!r}",
    )
    assert turn["opening_fallback_owner_bucket"] == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED
    assert turn["opening_fallback_authorship_source"] != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert meta.get("fallback_family_used") == "scene_opening"
    assert meta.get("realization_fallback_family") == "upstream_prepared_emission"
    assert meta.get("realization_fallback_family") != "legacy_diegetic_fallback"
    assert meta.get("fallback_family_used") != meta.get("realization_fallback_family")


def test_golden_canonical_opening_fallback_never_reports_compatibility_local_ownership():
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    meta = read_fem_meta_from_gate_output(out) or {}
    assert meta.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert opening_fallback_owner_bucket_from_meta(meta) == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


def test_golden_replay_lead_followup_with_dialogue_lock_structural_invariants(tmp_path, monkeypatch):
    responses = iter(
        [
            gm_response(
                'Tavern Runner says, "The patrol never came back from the old milestone beyond the east road."'
            ),
            gm_response('Tavern Runner says, "Last reliable sign was the old milestone."'),
        ]
    )

    def _fake_call_gpt(_messages):
        return next(responses)

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="lead_followup_with_dialogue_lock",
        turns=[
            "Tavern Runner, what happened to the patrol?",
            "Runner, where were they last seen?",
        ],
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_tavern_patrol_lead_world,
    )

    assert result["turn_count"] == 2
    turn = result["turns"][1]
    debug_context = format_golden_replay_debug(result)
    assert_protected_golden_turn_observation(
        turn,
        protected_social_structural_base(
            selected_speaker_id="tavern_runner",
            require_final_emitted_source=True,
            include_trace_route=True,
        ),
        scenario_id="lead_followup_with_dialogue_lock",
        debug_context=debug_context,
    )
    canonical_entry = (turn.get("trace") or {}).get("canonical_entry") or {}
    if canonical_entry:
        assert_protected_golden_turn_observation(
            turn,
            {
                **protected_unavailable_expectation("fallback_family"),
                "equals": {"trace.canonical_entry.target_actor_id": "tavern_runner"},
            },
            scenario_id="lead_followup_with_dialogue_lock",
            debug_context=debug_context,
        )


def test_golden_replay_frontier_gate_social_inquiry_25_turn_structural_stability(tmp_path, monkeypatch):
    turns = frontier_gate_branch_prompts("branch_social_inquiry")
    turn_ids = frontier_gate_branch_turn_ids("branch_social_inquiry")
    spine = load_frontier_gate_long_session_spine()
    assert len(turns) == 25

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return gm_response(
            (
                "The gate inquiry stays anchored: the notice board, Captain Thoran, the Ash Compact census "
                "delay, muddy footprints northwest of the crates, and the missing patrol route remain in view. "
                f"The answer advances the same thread at deterministic call {gpt_call_count}."
            )
        )

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="frontier_gate_social_inquiry_25_turn",
        turns=turns,
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_frontier_gate_world,
        starting_scene_id="frontier_gate",
        source_path=FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
        branch_id="branch_social_inquiry",
        turn_ids=turn_ids,
    )

    observed_turns = result["turns"]
    assert observed_turns[0]["source_path"] == FRONTIER_GATE_LONG_SESSION_SOURCE_PATH
    assert observed_turns[0]["branch_id"] == "branch_social_inquiry"
    assert observed_turns[0]["turn_id"] == "inv_01"
    assert observed_turns[-1]["turn_id"] == "inv_25"
    summary = summarize_long_session_replay_observations(observed_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id="branch_social_inquiry",
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_social_inquiry_25_turn",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 25-Turn Structural Stability",
            ),
        ]
    )
    assert f"source_path: {FRONTIER_GATE_LONG_SESSION_SOURCE_PATH!r}" in debug_context
    assert "branch_id: 'branch_social_inquiry'" in debug_context
    assert "turn_id: 'inv_01'" in debug_context

    assert result["turn_count"] == 25, debug_context
    assert summary["turn_count"] == 25, debug_context
    assert all(not turn.get("scaffold_leakage") for turn in observed_turns), debug_context
    assert summary["speaker_change_count"] <= 2, debug_context
    assert summary["speaker_missing_count"] <= 2, debug_context
    assert summary["fallback_turn_count"] <= 1, debug_context
    assert summary["fallback_owner_change_count"] <= 1, debug_context
    assert summary["route_change_count"] <= 2, debug_context

    route_frequency = summary["route_frequency"]
    resolved_routes = sum(route_frequency.values())
    assert resolved_routes >= 12, debug_context

    session_health = continuity_eval["session_health"]
    degradation = continuity_eval["degradation_over_time"]
    # The full 25-turn branch crosses the evaluator's long-session band; the prior
    # protected 20-turn slice was still classified as standard.
    assert session_health["long_session_band"] == "long", debug_context
    assert session_health["classification"] in {"clean", "warning"}, debug_context
    assert session_health["overall_passed"] is True, debug_context
    assert degradation["progressive_degradation_detected"] is False, debug_context
    assert "late_session_reset_or_amnesia" not in degradation["reason_codes"], debug_context
    assert "rising_generic_filler_strong" not in degradation["reason_codes"], debug_context
    assert "rising_generic_filler_progressive" not in degradation["reason_codes"], debug_context
    assert "debug_leak_late_window" not in degradation["reason_codes"], debug_context
    assert "referent_loss_late" not in degradation["reason_codes"], debug_context
    assert "continuity_anchor_late_loss" not in degradation["reason_codes"], debug_context
    assert continuity_eval["axes"]["narrative_grounding"]["passed"] is True, debug_context
    assert continuity_eval["axes"]["branch_coherence"]["passed"] is True, debug_context

    lineage_summary = summary["lineage_summary"]
    fallback_selected = lineage_summary.get("fallback_frequency") or {}
    assert sum(int(v) for v in fallback_selected.values()) <= 1, debug_context
    event_frequency = lineage_summary.get("by_event_kind") or {}
    assert int(event_frequency.get("fallback_selected") or 0) <= 1, debug_context
    assert int(event_frequency.get("mutation") or 0) <= 25, debug_context
    mutation_frequency = lineage_summary.get("mutation_kind_frequency") or {}
    assert int(mutation_frequency.get("fallback_mutation") or 0) <= 1, debug_context
    assert int(mutation_frequency.get("final_emission_mutation") or 0) <= 25, debug_context
    recurring_keys = {
        str(event.get("recurrence_key"))
        for event in lineage_summary.get("recurring_events", [])
        if isinstance(event, dict)
    }
    assert recurring_keys <= {
        "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
        "mutation:gate:game.final_emission_gate:final_emission_mutation",
    }, debug_context
    assert all(
        int(event.get("count") or 0) <= 25
        for event in lineage_summary.get("recurring_events", [])
        if isinstance(event, dict)
    ), debug_context

    fallback_escalation = summary["fallback_escalation_summary"]
    assert fallback_escalation["fallback_total_count"] <= 1, debug_context
    assert fallback_escalation["max_fallback_streak"] <= 1, debug_context
    assert fallback_escalation["late_window_fallback_count"] == 0, debug_context
    assert fallback_escalation["fallback_owner_change_count"] == 0, debug_context
    assert fallback_escalation["fallback_lineage_owner_change_count"] == 0, debug_context
    assert fallback_escalation["fallback_behavior_repair_count"] == 0, debug_context
    assert fallback_escalation["response_type_repair_count"] <= 1, debug_context
    assert fallback_escalation["sanitizer_fallback_count"] == 0, debug_context
    assert fallback_escalation["unavailable_with_fallback_count"] <= 1, debug_context
    assert fallback_escalation["fallback_selected_without_family_count"] <= 1, debug_context
    assert fallback_escalation["escalation_warnings"] == [], debug_context
    assert fallback_escalation["model_routing_escalation_observable"] is False, debug_context


def test_golden_replay_frontier_gate_social_inquiry_25_turn_resume_persistence_supporting(tmp_path, monkeypatch):
    # Supporting checkpoint probe: this uses a real on-disk snapshot restore at
    # the 12/13 boundary, but keeps the protected lock on the uninterrupted run.
    turns = frontier_gate_branch_prompts("branch_social_inquiry")
    turn_ids = frontier_gate_branch_turn_ids("branch_social_inquiry")
    spine = load_frontier_gate_long_session_spine()
    split_at = 12
    assert len(turns) == 25
    assert turn_ids[split_at - 1] == "inv_12"
    assert turn_ids[split_at] == "inv_13"

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return gm_response(
            (
                "The resumed gate inquiry stays anchored: the notice board, Captain Thoran, "
                "the Ash Compact census delay, muddy footprints northwest of the crates, "
                "and the missing patrol route remain in view. "
                f"The answer advances the same thread at deterministic call {gpt_call_count}."
            )
        )

    observed_turns = []
    checkpoint_meta = None
    restored_meta = None
    pre_resume_counter = None
    post_restore_counter = None
    post_restore_log_count = None

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    new_clean_campaign(starting_scene_id="frontier_gate")
    seed_frontier_gate_world()

    for i, text in enumerate(turns[:split_at]):
        payload = chat(ChatRequest(text=text))
        snap = snapshot_from_chat_payload(i, text, payload)
        observed_turns.append(
            _observed_turn(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                snap=snap,
                payload=payload,
                replay_identity={
                    "source_path": FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
                    "branch_id": "branch_social_inquiry",
                    "turn_id": turn_ids[i],
                },
            )
        )

    pre_resume_counter = int(storage.load_session().get("turn_counter") or 0)
    checkpoint_meta = storage.create_snapshot(label="golden-social-inquiry-after-turn-12")
    restored_meta = storage.load_snapshot(str(checkpoint_meta["id"]))
    post_restore_session = storage.load_session()
    post_restore_counter = int(post_restore_session.get("turn_counter") or 0)
    post_restore_log_count = len(storage.load_log())

    for i, text in enumerate(turns[split_at:], start=split_at):
        payload = chat(ChatRequest(text=text))
        snap = snapshot_from_chat_payload(i, text, payload)
        observed_turns.append(
            _observed_turn(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                snap=snap,
                payload=payload,
                replay_identity={
                    "source_path": FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
                    "branch_id": "branch_social_inquiry",
                    "turn_id": turn_ids[i],
                },
            )
        )

    result = {
        "scenario_id": "frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
        "turn_count": len(observed_turns),
        "turns": observed_turns,
    }
    pre_resume_turns = observed_turns[:split_at]
    post_resume_turns = observed_turns[split_at:]
    summary = summarize_long_session_replay_observations(observed_turns)
    pre_summary = summarize_long_session_replay_observations(pre_resume_turns)
    post_summary = summarize_long_session_replay_observations(post_resume_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id="branch_social_inquiry",
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            f"split_at: {split_at}",
            f"checkpoint_meta: {checkpoint_meta!r}",
            f"restored_meta: {restored_meta!r}",
            f"pre_resume_counter: {pre_resume_counter!r}",
            f"post_restore_counter: {post_restore_counter!r}",
            f"post_restore_log_count: {post_restore_log_count!r}",
            f"pre_resume_summary: {pre_summary!r}",
            f"post_resume_summary: {post_summary!r}",
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_social_inquiry_25_turn_resume_persistence_supporting",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 25-Turn Resume Persistence Supporting Probe",
            ),
        ]
    )

    assert checkpoint_meta is not None, debug_context
    assert restored_meta is not None, debug_context
    assert pre_resume_counter == split_at, debug_context
    assert post_restore_counter == split_at, debug_context
    assert post_restore_log_count == split_at, debug_context
    assert storage.load_session().get("turn_counter") == 25, debug_context
    assert len(storage.load_log()) == 25, debug_context

    assert result["turn_count"] == 25, debug_context
    assert summary["turn_count"] == 25, debug_context
    assert [turn.get("turn_index") for turn in observed_turns] == list(range(25)), debug_context
    assert [turn.get("turn_id") for turn in observed_turns] == turn_ids, debug_context
    assert observed_turns[split_at - 1]["turn_id"] == "inv_12", debug_context
    assert observed_turns[split_at]["turn_id"] == "inv_13", debug_context
    assert observed_turns[0]["source_path"] == FRONTIER_GATE_LONG_SESSION_SOURCE_PATH
    assert observed_turns[0]["branch_id"] == "branch_social_inquiry"
    assert observed_turns[-1]["turn_id"] == "inv_25"

    assert all(not turn.get("scaffold_leakage") for turn in observed_turns), debug_context
    assert pre_summary["turn_count"] == split_at, debug_context
    assert post_summary["turn_count"] == 25 - split_at, debug_context
    assert pre_summary["speaker_missing_count"] <= 2, debug_context
    assert post_summary["speaker_missing_count"] <= 1, debug_context
    assert observed_turns[split_at]["selected_speaker_id"] is not None, debug_context
    assert observed_turns[split_at]["selected_speaker_source"] is not None, debug_context
    assert summary["speaker_change_count"] <= 2, debug_context
    assert summary["speaker_missing_count"] <= 2, debug_context
    assert summary["fallback_turn_count"] <= 1, debug_context
    assert summary["fallback_owner_change_count"] <= 1, debug_context
    assert summary["route_change_count"] <= 2, debug_context

    session_health = continuity_eval["session_health"]
    degradation = continuity_eval["degradation_over_time"]
    assert session_health["long_session_band"] == "long", debug_context
    assert session_health["classification"] in {"clean", "warning"}, debug_context
    assert session_health["overall_passed"] is True, debug_context
    assert degradation["progressive_degradation_detected"] is False, debug_context
    assert "late_session_reset_or_amnesia" not in degradation["reason_codes"], debug_context
    assert "rising_generic_filler_strong" not in degradation["reason_codes"], debug_context
    assert "rising_generic_filler_progressive" not in degradation["reason_codes"], debug_context
    assert "debug_leak_late_window" not in degradation["reason_codes"], debug_context
    assert "referent_loss_late" not in degradation["reason_codes"], debug_context
    assert "continuity_anchor_late_loss" not in degradation["reason_codes"], debug_context
    assert continuity_eval["axes"]["narrative_grounding"]["passed"] is True, debug_context
    assert continuity_eval["axes"]["branch_coherence"]["passed"] is True, debug_context

    lineage_summary = summary["lineage_summary"]
    event_frequency = lineage_summary.get("by_event_kind") or {}
    mutation_frequency = lineage_summary.get("mutation_kind_frequency") or {}
    assert int(event_frequency.get("fallback_selected") or 0) <= 1, debug_context
    assert int(event_frequency.get("mutation") or 0) <= 25, debug_context
    assert int(mutation_frequency.get("fallback_mutation") or 0) <= 1, debug_context
    assert int(mutation_frequency.get("final_emission_mutation") or 0) <= 25, debug_context
    recurring_keys = {
        str(event.get("recurrence_key"))
        for event in lineage_summary.get("recurring_events", [])
        if isinstance(event, dict)
    }
    assert recurring_keys <= {
        "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
        "mutation:gate:game.final_emission_gate:final_emission_mutation",
    }, debug_context
    assert all(
        int(event.get("count") or 0) <= 25
        for event in lineage_summary.get("recurring_events", [])
        if isinstance(event, dict)
    ), debug_context

    fallback_escalation = summary["fallback_escalation_summary"]
    assert fallback_escalation["fallback_total_count"] <= 1, debug_context
    assert fallback_escalation["max_fallback_streak"] <= 1, debug_context
    assert fallback_escalation["late_window_fallback_count"] == 0, debug_context
    assert fallback_escalation["fallback_owner_change_count"] == 0, debug_context
    assert fallback_escalation["fallback_lineage_owner_change_count"] == 0, debug_context
    assert fallback_escalation["fallback_behavior_repair_count"] == 0, debug_context
    assert fallback_escalation["response_type_repair_count"] <= 1, debug_context
    assert fallback_escalation["sanitizer_fallback_count"] == 0, debug_context
    assert fallback_escalation["unavailable_with_fallback_count"] <= 1, debug_context
    assert fallback_escalation["fallback_selected_without_family_count"] <= 1, debug_context
    assert fallback_escalation["escalation_warnings"] == [], debug_context
    assert fallback_escalation["model_routing_escalation_observable"] is False, debug_context


def test_golden_replay_frontier_gate_direct_intrusion_25_turn_diagnostic_stability(tmp_path, monkeypatch):
    # Supporting diagnostic only: this branch intentionally stresses risky
    # action/visibility paths and currently emits more fallback lineage than the
    # protected social-inquiry baseline. Keep it supporting until it gets another
    # clean run after future fallback-family or action-routing changes.
    turns = frontier_gate_branch_prompts("branch_direct_intrusion")
    turn_ids = frontier_gate_branch_turn_ids("branch_direct_intrusion")
    spine = load_frontier_gate_long_session_spine()
    assert len(turns) == 25

    gpt_call_count = 0

    def _fake_call_gpt(_messages):
        nonlocal gpt_call_count
        gpt_call_count += 1
        return gm_response(
            (
                "The direct intrusion stays anchored: the gate serjeant, roster board, cordon pressure, "
                "warehouse latch, muddy crates, and watch whistles remain in view. "
                f"The risky push advances the same forced-access thread at deterministic call {gpt_call_count}."
            )
        )

    golden_replay_chat_stubs(monkeypatch, gpt_callback=_fake_call_gpt)

    result = run_golden_replay(
        scenario_id="frontier_gate_direct_intrusion_25_turn_diagnostic",
        turns=turns,
        tmp_path=tmp_path,
        monkeypatch=monkeypatch,
        setup_fn=seed_frontier_gate_world,
        starting_scene_id="frontier_gate",
        source_path=FRONTIER_GATE_LONG_SESSION_SOURCE_PATH,
        branch_id="branch_direct_intrusion",
        turn_ids=turn_ids,
    )

    observed_turns = result["turns"]
    assert observed_turns[0]["source_path"] == FRONTIER_GATE_LONG_SESSION_SOURCE_PATH
    assert observed_turns[0]["branch_id"] == "branch_direct_intrusion"
    assert observed_turns[0]["turn_id"] == "act_01"
    assert observed_turns[-1]["turn_id"] == "act_25"
    summary = summarize_long_session_replay_observations(observed_turns)
    continuity_bridge = evaluate_golden_replay_continuity_drift(
        spine=spine,
        branch_id="branch_direct_intrusion",
        turns=observed_turns,
        turn_ids=turn_ids,
    )
    continuity_eval = continuity_bridge["evaluation"]
    summary["continuity_drift"] = continuity_eval
    debug_context = "\n\n".join(
        [
            format_golden_replay_debug(result),
            render_long_session_replay_summary_markdown(
                scenario_id="frontier_gate_direct_intrusion_25_turn_diagnostic",
                turns=observed_turns,
                summary=summary,
                title="Golden Replay 25-Turn Direct-Intrusion Diagnostic Stability",
            ),
        ]
    )
    assert f"source_path: {FRONTIER_GATE_LONG_SESSION_SOURCE_PATH!r}" in debug_context
    assert "branch_id: 'branch_direct_intrusion'" in debug_context
    assert "turn_id: 'act_01'" in debug_context

    assert result["turn_count"] == 25, debug_context
    assert summary["turn_count"] == 25, debug_context
    assert all(not turn.get("scaffold_leakage") for turn in observed_turns), debug_context
    assert summary["route_change_count"] <= 6, debug_context
    assert summary["speaker_change_count"] <= 3, debug_context
    assert summary["speaker_missing_count"] <= 20, debug_context
    assert summary["fallback_turn_count"] == 7, debug_context
    assert summary["fallback_owner_change_count"] == 0, debug_context
    assert summary["mutation_turn_count"] <= 25, debug_context

    session_health = continuity_eval["session_health"]
    degradation = continuity_eval["degradation_over_time"]
    assert session_health["long_session_band"] == "long", debug_context
    assert session_health["classification"] in {"clean", "warning"}, debug_context
    assert session_health["overall_passed"] is True, debug_context
    assert degradation["progressive_degradation_detected"] is False, debug_context
    assert "late_session_reset_or_amnesia" not in degradation["reason_codes"], debug_context
    assert "rising_generic_filler_strong" not in degradation["reason_codes"], debug_context
    assert "rising_generic_filler_progressive" not in degradation["reason_codes"], debug_context
    assert "debug_leak_late_window" not in degradation["reason_codes"], debug_context
    assert "referent_loss_late" not in degradation["reason_codes"], debug_context
    assert "continuity_anchor_late_loss" not in degradation["reason_codes"], debug_context
    assert continuity_eval["axes"]["narrative_grounding"]["passed"] is True, debug_context
    assert continuity_eval["axes"]["branch_coherence"]["passed"] is True, debug_context

    lineage_summary = summary["lineage_summary"]
    fallback_frequency = summary["fallback_frequency"]
    assert set(fallback_frequency) <= {
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
        "gate_terminal_repair",
    }, debug_context
    assert int(fallback_frequency.get(NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY) or 0) <= 4, debug_context
    assert int(fallback_frequency.get("gate_terminal_repair") or 0) <= 3, debug_context
    event_frequency = lineage_summary.get("by_event_kind") or {}
    mutation_frequency = lineage_summary.get("mutation_kind_frequency") or {}
    assert int(event_frequency.get("fallback_selected") or 0) == 7, debug_context
    assert int(event_frequency.get("mutation") or 0) <= 14, debug_context
    assert int(event_frequency.get("speaker_repair") or 0) <= 1, debug_context
    assert int(mutation_frequency.get("fallback_mutation") or 0) <= 7, debug_context
    assert int(mutation_frequency.get("final_emission_mutation") or 0) <= 4, debug_context
    assert int(mutation_frequency.get("response_type_repair_mutation") or 0) <= 2, debug_context
    assert int(mutation_frequency.get("speaker_repair_mutation") or 0) <= 1, debug_context
    recurring_keys = {
        str(event.get("recurrence_key"))
        for event in lineage_summary.get("recurring_events", [])
        if isinstance(event, dict)
    }
    allowed_recurring_keys = {
        "gate_outcome:gate:game.final_emission_gate:accept_unchanged",
        "mutation:gate:game.final_emission_gate:fallback_mutation",
        "fallback_selected:gate:game.final_emission_gate:sealed_or_global_replacement",
        "gate_outcome:gate:game.final_emission_gate:replaced_or_sealed",
        "gate_outcome:gate:game.final_emission_gate:strict_social_accept",
        "mutation:gate:game.final_emission_gate:final_emission_mutation",
        "fallback_selected:gate:game.final_emission_gate:response_type_prepared_emission",
        "gate_outcome:gate:game.final_emission_gate:prepared_repair",
        "mutation:gate:game.final_emission_gate:response_type_repair_mutation",
    } | {
        f"fallback_selected:gate:game.final_emission_gate:{subkind}"
        for subkind in SEALED_REPLACEMENT_SUBKINDS
    }
    assert recurring_keys <= allowed_recurring_keys, debug_context
    assert all(
        int(event.get("count") or 0) <= 25
        for event in lineage_summary.get("recurring_events", [])
        if isinstance(event, dict)
    ), debug_context

    fallback_escalation = summary["fallback_escalation_summary"]
    assert fallback_escalation["fallback_total_count"] == 7, debug_context
    assert set(fallback_escalation["fallback_family_counts"]) <= {
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
        "gate_terminal_repair",
    }, debug_context
    assert fallback_escalation["fallback_family_counts"].get(
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY
    ) == 4, debug_context
    assert fallback_escalation["fallback_family_counts"].get("gate_terminal_repair") == 3, debug_context
    assert fallback_escalation["max_fallback_streak"] <= 2, debug_context
    assert fallback_escalation["max_scene_action_nonblocking_fallback_streak"] <= 2, debug_context
    assert fallback_escalation["max_blocking_fallback_streak"] == 0, debug_context
    assert fallback_escalation["late_window_fallback_count"] <= 2, debug_context
    assert fallback_escalation["fallback_owner_change_count"] == 0, debug_context
    assert fallback_escalation["fallback_lineage_owner_change_count"] == 0, debug_context
    assert fallback_escalation["fallback_behavior_repair_count"] == 0, debug_context
    assert fallback_escalation["response_type_repair_count"] <= 2, debug_context
    assert fallback_escalation["sanitizer_fallback_count"] == 0, debug_context
    assert fallback_escalation["unavailable_with_fallback_count"] <= 7, debug_context
    assert fallback_escalation["scene_action_speaker_optional_unavailable_count"] == 7, debug_context
    assert fallback_escalation["blocking_unavailable_with_fallback_count"] == 0, debug_context
    assert fallback_escalation["fallback_selected_without_family_count"] == 0, debug_context
    assert fallback_escalation["escalation_warnings"] == [], debug_context
    assert fallback_escalation["model_routing_escalation_observable"] is False, debug_context


def test_golden_replay_scenario_spine_three_branch_structural_smoke(tmp_path, monkeypatch):
    spine = ScenarioSpine(
        spine_id="golden_smoke_frontier_gate",
        title="Golden smoke three branch spine",
        smoke_only=True,
        fixed_start_state={"scene_id": "scene_investigate"},
        branches=(
            ScenarioBranch(
                branch_id="branch_runner_question",
                label="Ask the runner",
                turns=(ScenarioTurn(turn_id="runner_ask", player_prompt="Runner, who attacked the patrol?"),),
            ),
            ScenarioBranch(
                branch_id="branch_guard_question",
                label="Ask the guard",
                turns=(ScenarioTurn(turn_id="guard_ask", player_prompt="Guard, what did you see?"),),
            ),
            ScenarioBranch(
                branch_id="branch_notice_check",
                label="Check the notice",
                turns=(
                    ScenarioTurn(
                        turn_id="notice_check",
                        player_prompt="I examine the notice board; does it show where the missing patrol went?",
                    ),
                ),
            ),
        ),
    )
    assert validate_scenario_spine_definition(spine) == []
    spine_dict = scenario_spine_to_dict(spine)

    def _fake_call_gpt(_messages):
        return gm_response('Tavern Runner says, "The east road keeps the best clue."')

    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=_fake_call_gpt,
        suppress_exploration=False,
        suppress_intent=False,
    )

    branch_rows: list[dict] = []
    for branch in spine.branches:
        result = run_golden_replay(
            scenario_id=f"scenario_spine_three_branch::{branch.branch_id}",
            turns=[turn.player_prompt for turn in branch.turns],
            tmp_path=tmp_path / branch.branch_id,
            monkeypatch=monkeypatch,
            setup_fn=seed_spine_three_branch_world,
        )
        assert result["turn_count"] == len(branch.turns)
        for i, turn in enumerate(result["turns"]):
            meta = minimal_complete_transcript_turn_meta(
                spine_id=spine.spine_id,
                branch_id=branch.branch_id,
                turn_id=branch.turns[i].turn_id,
                turn_index=i,
                smoke=True,
                max_turns=len(branch.turns),
            )
            assert meta["scenario_spine"]["branch_id"] == branch.branch_id
            assert_golden_turn_observation(
                turn,
                {
                    **protected_structural_expectation(
                        require_present=("final_text",),
                        allow_unavailable=(
                            "fallback_family",
                            "selected_speaker_id",
                            "final_emitted_source",
                            "trace.canonical_entry",
                            "trace.social_contract_trace",
                        ),
                        no_scaffold=False,
                        include_route_kind=False,
                    ),
                    "scaffold_leakage": False,
                },
                debug_context=format_golden_replay_debug(result),
            )
        last = result["turns"][-1]
        branch_rows.append(
            {
                "branch_id": branch.branch_id,
                "turn_count": result["turn_count"],
                "route_kind": last.get("route_kind"),
                "selected_speaker_id": last.get("selected_speaker_id"),
                "final_emitted_source": last.get("final_emitted_source"),
                "fallback_family": last.get("fallback_family"),
            }
        )

    assert [row["branch_id"] for row in branch_rows] == [branch.branch_id for branch in spine.branches]
    assert {row["turn_count"] for row in branch_rows} == {1}
    assert len({(row["route_kind"], row["selected_speaker_id"]) for row in branch_rows}) >= 2
    assert [b["branch_id"] for b in spine_dict["branches"]] == sorted(row["branch_id"] for row in branch_rows)
