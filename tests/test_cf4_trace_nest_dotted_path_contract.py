"""CF4 — table-driven contracts for trace nest and dotted protected paths."""
from __future__ import annotations

import pytest

from tests.helpers.golden_replay_fixtures import minimal_gm_output_payload, minimal_turn_payload, project_synthetic_turn
from tests.helpers.golden_replay_projection import (
    lookup_observation_path,
    protected_observation_extraction_registry,
    protected_observation_field_registry,
    protected_observation_manifest_field_rows,
)
from tests.helpers.golden_replay_projection_extractors import (
    MISSING,
    protected_path_covered_by_unavailable,
    protected_path_representation_errors,
)
from tests.helpers.golden_replay_projection_fields import protected_observation_field_paths
from tests.helpers.trace_nest_contract import (
    build_dotted_path_matrix,
    build_trace_container_matrix,
    dotted_protected_field_paths,
    flat_protected_field_paths,
    trace_container_unavailable_keys,
    trace_diagnostic_only_observed_keys,
)

pytestmark = pytest.mark.unit

_DOTTED = dotted_protected_field_paths()
_MATRIX = build_dotted_path_matrix()
_CONTAINERS = build_trace_container_matrix()

_RICH_TRACE_PAYLOAD = {
    **minimal_gm_output_payload(),
    "debug_traces": [
        {
            "canonical_entry": {
                "target_actor_id": "runner",
                "target_source": "social",
                "reason": "direct_vocative",
            },
            "turn_trace": {
                "social_contract_trace": {"route_selected": "dialogue"},
            },
            "canonical_entry_path": "interaction_context",
            "canonical_entry_reason": "direct_vocative",
            "canonical_entry_target_actor_id": "runner",
        }
    ],
}


def test_cf4_flat_vs_dotted_inventory_counts() -> None:
    assert len(flat_protected_field_paths()) == 37
    assert len(_DOTTED) == 4
    assert len(flat_protected_field_paths()) + len(_DOTTED) == len(protected_observation_field_paths()) == 41


def test_cf4_dotted_matrix_covers_all_dotted_protected_paths() -> None:
    assert {row.protected_path for row in _MATRIX} == set(_DOTTED)


@pytest.mark.parametrize(
    "path,expected",
    [
        ("trace.canonical_entry.target_actor_id", "runner"),
        ("trace.canonical_entry.target_source", "social"),
        ("trace.canonical_entry.reason", "direct_vocative"),
        ("trace.social_contract_trace.route_selected", "dialogue"),
    ],
)
def test_cf4_dotted_path_extraction_rich_trace(path: str, expected: str) -> None:
    observed = project_synthetic_turn(
        scenario_id="cf4_rich_trace",
        gm_text="The runner nods.",
        payload=_RICH_TRACE_PAYLOAD,
    )
    assert lookup_observation_path(observed, path) == expected


def test_cf4_social_contract_trace_normalized_from_turn_trace_nest() -> None:
    observed = project_synthetic_turn(
        scenario_id="cf4_nested_social_contract",
        gm_text="Hello.",
        payload=_RICH_TRACE_PAYLOAD,
    )
    trace = observed["trace"]
    assert trace["social_contract_trace"] == {"route_selected": "dialogue"}
    assert "social_contract_trace" in trace["turn_trace"]
    assert lookup_observation_path(observed, "trace.social_contract_trace.route_selected") == "dialogue"


def test_cf4_sparse_trace_containers_unavailable() -> None:
    observed = project_synthetic_turn(
        scenario_id="cf4_sparse_trace",
        gm_text="Quiet road.",
    )
    assert set(trace_container_unavailable_keys()) <= set(observed["unavailable"])
    for container in trace_container_unavailable_keys():
        assert observed["raw_signal_presence"][container] is False


@pytest.mark.parametrize("path", _DOTTED)
def test_cf4_dotted_paths_covered_when_parent_unavailable(path: str) -> None:
    observed = project_synthetic_turn(
        scenario_id="cf4_sparse_parent_unavailable",
        gm_text="Quiet.",
    )
    unavailable = frozenset(observed["unavailable"])
    assert protected_path_covered_by_unavailable(path, unavailable) is True


def test_cf4_parent_unavailable_child_lookup_missing_but_represented() -> None:
    observed = project_synthetic_turn(
        scenario_id="cf4_parent_unavail_representation",
        gm_text="Quiet.",
    )
    path = "trace.canonical_entry.target_actor_id"
    assert lookup_observation_path(observed, path) is MISSING
    assert protected_path_representation_errors(observed) == []


def test_cf4_malformed_canonical_entry_becomes_empty_container() -> None:
    observed = project_synthetic_turn(
        scenario_id="cf4_malformed_canonical",
        gm_text="Hello.",
        payload={
            **minimal_gm_output_payload(),
            "debug_traces": [{"canonical_entry": "not-a-mapping"}],
        },
    )
    assert observed["trace"]["canonical_entry"] == {}
    assert "trace.canonical_entry" in observed["unavailable"]
    assert lookup_observation_path(observed, "trace.canonical_entry.target_actor_id") is MISSING


def test_cf4_snapshot_fallback_populates_trace_when_payload_traces_absent() -> None:
    observed = project_turn_observation_from_snap_trace(
        canonical_entry={"target_actor_id": "snap_npc", "target_source": "snap", "reason": "snap_reason"},
        social_contract={"route_selected": "social"},
    )
    assert lookup_observation_path(observed, "trace.canonical_entry.target_actor_id") == "snap_npc"
    assert lookup_observation_path(observed, "trace.social_contract_trace.route_selected") == "social"
    assert "trace.canonical_entry" not in observed["unavailable"]


def test_cf4_partial_trace_canonical_only_clears_social_unavailable() -> None:
    observed = project_synthetic_turn(
        scenario_id="cf4_partial_canonical_only",
        gm_text="Hello.",
        payload={
            **minimal_gm_output_payload(),
            "debug_traces": [
                {
                    "canonical_entry": {
                        "target_actor_id": "runner",
                        "target_source": "social",
                        "reason": "direct",
                    },
                }
            ],
        },
    )
    assert "trace.canonical_entry" not in observed["unavailable"]
    assert "trace.social_contract_trace" in observed["unavailable"]
    assert lookup_observation_path(observed, "trace.canonical_entry.target_actor_id") == "runner"
    assert lookup_observation_path(observed, "trace.social_contract_trace.route_selected") is MISSING


def test_cf4_diagnostic_trace_keys_are_not_protected_registry_paths() -> None:
    observed = project_synthetic_turn(
        scenario_id="cf4_diagnostic_keys",
        gm_text="Hello.",
        payload=_RICH_TRACE_PAYLOAD,
    )
    diagnostic = trace_diagnostic_only_observed_keys()
    registry_paths = set(protected_observation_field_paths())
    for key in diagnostic:
        assert key not in registry_paths
        assert key in observed["trace"]


@pytest.mark.parametrize("path", _DOTTED)
def test_cf4_registry_schema_manifest_parity(path: str) -> None:
    registry = {field.path: field.drift_bucket for field in protected_observation_field_registry()}
    assert path in registry
    assert path in protected_observation_extraction_registry()
    manifest = dict(protected_observation_manifest_field_rows())
    assert manifest[path] == registry[path] == "structural_drift"


def test_cf4_trace_container_matrix_leaf_mapping() -> None:
    canonical = next(row for row in _CONTAINERS if row.observed_key == "canonical_entry")
    social = next(row for row in _CONTAINERS if row.observed_key == "social_contract_trace")
    turn = next(row for row in _CONTAINERS if row.observed_key == "turn_trace")
    assert len(canonical.protected_leaf_paths) == 3
    assert len(social.protected_leaf_paths) == 1
    assert turn.protected_leaf_paths == ()
    assert canonical.diagnostic_keys == (
        "canonical_entry_path",
        "canonical_entry_reason",
        "canonical_entry_target_actor_id",
    )


def test_cf4_rich_trace_representation_errors_empty() -> None:
    observed = project_synthetic_turn(
        scenario_id="cf4_rich_representation",
        gm_text="The runner speaks.",
        payload=_RICH_TRACE_PAYLOAD,
    )
    assert protected_path_representation_errors(observed) == []
    for container in trace_container_unavailable_keys():
        assert container not in observed["unavailable"]


def project_turn_observation_from_snap_trace(
    *,
    canonical_entry: dict[str, str],
    social_contract: dict[str, str],
) -> dict[str, object]:
    from tests.helpers.golden_replay_projection import project_turn_observation

    return project_turn_observation(
        {
            "scenario_id": "cf4_snap_trace_fallback",
            "snap": {
                "gm_text": "Snap trace.",
                "turn_index": 0,
                "debug": {
                    "last_debug_trace": {
                        "canonical_entry": canonical_entry,
                        "turn_trace": {"social_contract_trace": social_contract},
                    }
                },
            },
            "payload": minimal_gm_output_payload(),
        }
    )
