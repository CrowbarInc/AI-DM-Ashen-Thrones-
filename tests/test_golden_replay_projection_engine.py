"""CL7 projection engine extraction parity tests."""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

import tests.helpers.golden_replay_projection_engine as engine
import tests.helpers.golden_replay_projection_extractors as extractors
from tests.helpers.golden_replay_fixtures import minimal_turn_payload, project_synthetic_turn
from tests.helpers.golden_replay_projection import project_turn_observation
from tests.helpers.golden_replay_projection_test_support import ak5_rich_projection_payload

pytestmark = pytest.mark.unit

BACKUP_PATH = Path(__file__).resolve().parents[1] / "tests" / "helpers" / "golden_replay_projection.py.bak"


def _load_backup_module():
    source = BACKUP_PATH.read_text(encoding="utf-8")
    mod = types.ModuleType("golden_replay_projection_backup_for_engine")
    sys.modules[mod.__name__] = mod
    exec(compile(source, str(BACKUP_PATH), "exec"), mod.__dict__)
    return mod


def _stable_json(row: dict) -> str:
    return json.dumps(
        row,
        ensure_ascii=False,
        separators=(",", ":"),
        default=lambda _value: "<non_json_sentinel>",
    )


def test_cl7_projected_rows_remain_byte_for_byte_identical_to_backup():
    backup = _load_backup_module()
    sparse_payload = minimal_turn_payload(
        scenario_id="cl7_sparse_projection",
        gm_text="Rain beads on the gate stones.",
    )
    rich_payload = project_synthetic_turn(
        scenario_id="cl7_rich_projection",
        gm_text="The runner says the patrol moved east.",
        player_text="Ask the runner.",
        resolution={"kind": "question", "social": {"npc_id": "runner"}},
        payload=ak5_rich_projection_payload(),
    )

    for payload in (sparse_payload, rich_payload):
        assert _stable_json(project_turn_observation(payload)) == _stable_json(
            backup.project_turn_observation(payload)
        )


def test_cl7_flat_projection_ordering_unchanged_from_backup():
    backup = _load_backup_module()
    fem = {
        "final_emitted_source": "terminal",
        "final_emission_mutation_lineage": ("a", "b"),
        "response_type_required": True,
        "fallback_temporal_frame": "present",
    }
    sanitizer_trace_flat = {
        "sanitizer_empty_fallback_used": False,
        "sanitizer_strict_social_source": "none",
    }
    sanitizer_lineage_flat = {
        "sanitizer_lineage_mode": "boundary",
        "sanitizer_lineage_changed_count": 1,
        "sanitizer_lineage_dropped_count": 0,
        "sanitizer_lineage_empty_fallback_used": False,
        "sanitizer_lineage_legacy_rewrite_active": False,
    }
    kwargs = dict(
        resolution={"kind": "observe"},
        route_kind="observe",
        selected_speaker_id="guard",
        fem=fem,
        fem_flat=engine._extract_fem_flat_observed_fields(fem),
        sanitizer_trace_flat=sanitizer_trace_flat,
        sanitizer_lineage_flat=sanitizer_lineage_flat,
        fallback_family="observe",
        final_text="The guard watches the rain.",
    )

    current = engine._project_flat_protected_observed_fields(**kwargs)
    previous = backup._project_flat_protected_observed_fields(**kwargs)

    assert tuple(current) == tuple(previous)
    assert _stable_json(current) == _stable_json(previous)


def test_cl7_engine_extraction_helpers_match_previous_implementation():
    backup = _load_backup_module()
    fem = {
        "final_route": "fallback_route",
        "response_type_required": True,
        "final_emission_mutation_lineage": ["raw"],
    }
    sanitizer_trace = {
        "sanitizer_empty_fallback_used": True,
        "sanitizer_empty_fallback_source": "empty",
        "sanitizer_lineage_mode": "legacy_sentence_rewrite",
        "sanitizer_lineage_changed_count": 2,
    }
    lineage_context = {
        "sanitizer_mode": "context_mode",
        "sanitizer_changed_count": 1,
        "sanitizer_dropped_count": 0,
        "sanitizer_empty_fallback_used": True,
    }

    assert engine._extract_fem_flat_observed_fields(fem) == backup._extract_fem_flat_observed_fields(fem)
    assert engine._extract_sanitizer_trace_flat_observed_fields(
        sanitizer_trace
    ) == backup._extract_sanitizer_trace_flat_observed_fields(sanitizer_trace)
    assert engine._extract_sanitizer_lineage_observed_fields(
        sanitizer_trace,
        lineage_context=lineage_context,
    ) == backup._extract_sanitizer_lineage_observed_fields(
        sanitizer_trace,
        lineage_context=lineage_context,
    )
    assert engine._resolve_route_kind(
        social_contract_trace={"route_selected": "trace_route"},
        resolution_compact={"kind": "compact_route"},
        resolution={"kind": "resolution_route"},
    ) == backup._resolve_route_kind(
        social_contract_trace={"route_selected": "trace_route"},
        resolution_compact={"kind": "compact_route"},
        resolution={"kind": "resolution_route"},
    )


def test_cl7_extractor_compatibility_reexports_engine_symbols():
    assert extractors._extract_fem_flat_observed_fields is engine._extract_fem_flat_observed_fields
    assert extractors._extract_sanitizer_trace_flat_observed_fields is (
        engine._extract_sanitizer_trace_flat_observed_fields
    )
    assert extractors._extract_sanitizer_lineage_observed_fields is (
        engine._extract_sanitizer_lineage_observed_fields
    )
    assert extractors._project_flat_protected_observed_fields is engine._project_flat_protected_observed_fields
    assert extractors._resolve_route_kind is engine._resolve_route_kind
    assert extractors._validate_protected_projection_sources is engine._validate_protected_projection_sources
