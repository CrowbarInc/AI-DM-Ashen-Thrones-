"""Unit tests for ``tools/test_audit.py`` helpers (no full-suite pytest collect)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[1]
TOOL_PATH = ROOT / "tools" / "test_audit.py"
INVENTORY_PATH = ROOT / "tests" / "test_inventory_governance.json"
GOVERNANCE_FIXTURE_PATH = "tests/test_final_emission_gate.py"
NON_REGISTRY_FIXTURE_PATH = "tests/test_non_registry_module.py"


def _governance_file_row(*, path: str = GOVERNANCE_FIXTURE_PATH, layer: str = "gate") -> dict:
    return {
        "path": path,
        "marker_set": ["unit"],
        "collected_duplicate_base_names": [],
        "likely_architecture_layer": layer,
        "pytest_collected": 1,
    }


def _minimal_inventory(*, generated_utc: str = "2026-01-01T00:00:00+00:00", inventory_kind: str = "governance") -> dict:
    return {
        "summary": {
            "inventory_schema_version": 2,
            "inventory_kind": inventory_kind,
            "declared_pytest_markers": ["unit"],
        },
        "files": [_governance_file_row()],
    }


def _minimal_full_inventory(*, generated_utc: str = "2026-01-01T00:00:00+00:00") -> dict:
    gov = _minimal_inventory(generated_utc=generated_utc, inventory_kind="full")
    gov["files"] = [
        {
            **_governance_file_row(),
            "collected_nodeids": [f"{GOVERNANCE_FIXTURE_PATH}::test_ok"],
            "overlap_hints": ["module_shadowed_duplicate_test_names"],
        },
        {
            **_governance_file_row(path=NON_REGISTRY_FIXTURE_PATH, layer="engine"),
            "collected_nodeids": [f"{NON_REGISTRY_FIXTURE_PATH}::test_other"],
            "overlap_hints": [],
        },
    ]
    gov["tests"] = [
        {
            "nodeid": f"{GOVERNANCE_FIXTURE_PATH}::test_ok",
            "file": GOVERNANCE_FIXTURE_PATH,
            "name": "test_ok",
            "base_name": "test_ok",
            "parametrized": False,
            "marker_set": ["unit"],
            "brittleness": "low",
        },
        {
            "nodeid": f"{NON_REGISTRY_FIXTURE_PATH}::test_other",
            "file": NON_REGISTRY_FIXTURE_PATH,
            "name": "test_other",
            "base_name": "test_other",
            "parametrized": False,
            "marker_set": ["unit"],
            "brittleness": "low",
        },
    ]
    gov["feature_areas_by_distinct_files"] = []
    gov["block_b_overlap_clusters"] = [{"kind": "dense_ownership_theme_by_architecture_layer", "cells": []}]
    gov["import_hub_modules"] = [{"game_module": "game.api", "file_count": 12, "sample_files": [GOVERNANCE_FIXTURE_PATH]}]
    gov["cross_file_duplicate_test_names"] = []
    gov["summary"]["test_file_count"] = 2
    gov["summary"]["pytest_collected_items"] = 2
    gov["summary"]["generated_utc"] = generated_utc
    return gov


@pytest.fixture(scope="module")
def audit_mod():
    name = "_test_audit_tool_under_test"
    spec = importlib.util.spec_from_file_location(name, TOOL_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_parse_game_import_from_game_package(audit_mod) -> None:
    src = "from game import api\nfrom game.final_emission_gate import apply_final_emission_gate\n"
    mods = audit_mod._parse_game_import_modules(src)
    assert "game.api" in mods
    assert "game.final_emission_gate" in mods


def test_game_import_roots_dedupes(audit_mod) -> None:
    roots = audit_mod._game_import_roots(["game.final_emission_gate", "game.final_emission_repairs", "game.api"])
    assert sorted(roots) == ["api", "final_emission_gate", "final_emission_repairs"]


def test_architecture_layer_prefers_transcript_signals(audit_mod) -> None:
    fp = "tests/test_mixed_state_recovery_regressions.py"
    src = "from tests.helpers.transcript_runner import run_transcript\n"
    scores = audit_mod._architecture_layer_scores(fp, src, "regression")
    assert audit_mod._primary_architecture_layer(scores) == "transcript"


def test_architecture_layer_prefers_gate_when_gate_imported(audit_mod) -> None:
    fp = "tests/test_final_emission_gate.py"
    src = "from game.final_emission_gate import apply_final_emission_gate\n"
    scores = audit_mod._architecture_layer_scores(fp, src, "mixed/unclear")
    assert scores["gate"] >= 8
    assert audit_mod._primary_architecture_layer(scores) == "gate"


def test_architecture_layer_smoke_filename(audit_mod) -> None:
    fp = "tests/test_behavioral_gauntlet_smoke.py"
    src = "# no imports\n"
    scores = audit_mod._architecture_layer_scores(fp, src, "mixed/unclear")
    assert audit_mod._primary_architecture_layer(scores) == "smoke"


def test_likely_ownership_theme_uses_majority_feature(audit_mod) -> None:
    theme = audit_mod._likely_ownership_theme(
        "tests/test_clue_knowledge.py",
        {"clue system": 5, "general": 1},
        ["clue"],
    )
    assert "clue" in theme.lower()


def test_overlap_hints_surface_shadowing(audit_mod) -> None:
    hints = audit_mod._overlap_hints_for_file(
        "tests/test_x.py",
        "from game.final_emission_gate import x\nfrom game.prompt_context import y\n",
        ["game.final_emission_gate", "game.prompt_context"],
        ["final_emission_gate", "prompt_context"],
        True,
        ["test_dup_name"],
        "routing",
        "gate",
    )
    joined = " ".join(hints)
    assert "module_shadowed_duplicate_test_names" in joined
    assert "cross_file_same_test_base_name" in joined
    assert "gate_stack_adjacent_to_prompt_context" in joined


def test_keyword_overlap_hints_multi_hit(audit_mod) -> None:
    body = "route routing dialogue_lock"
    hints = audit_mod._test_keyword_overlap_hints("tests/test_foo.py::test_bar", body)
    assert any(h.startswith("multi_keyword:") for h in hints)


def test_declared_markers_from_ini_includes_core_lanes(audit_mod) -> None:
    m = audit_mod._declared_markers_from_pytest_ini()
    assert "unit" in m
    assert "transcript" in m
    assert "emission" in m


def test_parse_module_marks_detects_pytestmark_and_per_test(audit_mod, tmp_path) -> None:
    p = tmp_path / "sample_tests.py"
    p.write_text(
        "import pytest\n\n"
        "pytestmark = [pytest.mark.integration, pytest.mark.slow]\n\n"
        "@pytest.mark.unit\n"
        "def test_foo():\n"
        "    assert True\n",
        encoding="utf-8",
    )
    mod_marks, per_test = audit_mod._parse_module_pytestmarks_and_per_test_marks(p)
    assert "integration" in mod_marks and "slow" in mod_marks
    assert per_test.get("test_foo") == ["unit"]


def test_architecture_layer_weak_signal_is_general(audit_mod) -> None:
    fp = "tests/test_misc_helpers.py"
    src = "# no game imports, no client, no tmp_path\n"
    scores = audit_mod._architecture_layer_scores(fp, src, "mixed/unclear")
    assert audit_mod._primary_architecture_layer(scores) == "general"


def test_build_ownership_registry_index_exports_groups_and_roles(audit_mod) -> None:
    idx = audit_mod._build_ownership_registry_index()
    assert idx is not None
    assert idx.get("available") is True
    assert isinstance(idx.get("groups"), dict)
    assert "final_emission_gate_orchestration" in idx["groups"]
    gate = idx["groups"]["final_emission_gate_orchestration"]
    assert "downstream_consumer_suites" in gate and "compatibility_residue_suites" in gate
    roles = idx.get("files_roles")
    assert isinstance(roles, dict)
    assert any("tests/test_final_emission_gate.py" == p for p in roles)


def test_normalize_inventory_ignores_generated_utc(audit_mod) -> None:
    a = _minimal_inventory()
    b = _minimal_inventory()
    b["summary"]["declared_pytest_markers"] = list(a["summary"]["declared_pytest_markers"])
    assert audit_mod.normalize_inventory_for_compare(a) == audit_mod.normalize_inventory_for_compare(b)


def test_inventories_match_when_only_timestamp_differs(audit_mod) -> None:
    a = _minimal_inventory()
    b = _minimal_inventory()
    assert audit_mod.inventories_match_excluding_timestamp(a, b)


def test_inventories_do_not_match_when_file_rows_differ(audit_mod) -> None:
    committed = _minimal_inventory()
    fresh = _minimal_inventory()
    fresh["files"] = [dict(fresh["files"][0], likely_architecture_layer="engine")]
    assert not audit_mod.inventories_match_excluding_timestamp(fresh, committed)


def test_format_inventory_drift_report_lists_nodeid_and_file_deltas(audit_mod) -> None:
    committed = _minimal_inventory()
    fresh = _minimal_inventory()
    fresh["files"] = list(committed["files"]) + [
        {
            "path": "tests/test_new_module.py",
            "marker_set": [],
            "collected_duplicate_base_names": [],
            "likely_architecture_layer": "engine",
            "pytest_collected": 1,
        }
    ]
    fresh["summary"] = dict(committed["summary"])
    fresh["summary"]["inventory_schema_version"] = 3

    report = audit_mod.format_inventory_drift_report(
        fresh,
        committed,
        artifact_path=Path("tests/test_inventory_governance.json"),
    )
    joined = "\n".join(report)
    assert "tests/test_new_module.py" in joined
    assert "derived at check time" in joined or "added" in joined
    assert "generated_utc" in joined


def test_run_inventory_check_passes_when_committed_matches_fresh(audit_mod, tmp_path: Path, monkeypatch) -> None:
    inv_path = tmp_path / "test_inventory_governance.json"
    full = _minimal_full_inventory(generated_utc="2026-01-01T00:00:00+00:00")
    gov = audit_mod.build_governance_payload(full)
    inv_path.write_text(json.dumps(gov, indent=2, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(audit_mod, "GOVERNANCE_JSON", inv_path)
    monkeypatch.setattr(
        audit_mod,
        "build_inventory_payload",
        lambda: _minimal_full_inventory(generated_utc="2026-06-04T12:34:56+00:00"),
    )
    assert audit_mod.run_inventory_check() == 0


def test_run_inventory_check_fails_when_committed_stale(audit_mod, tmp_path: Path, monkeypatch) -> None:
    inv_path = tmp_path / "test_inventory_governance.json"
    committed = _minimal_inventory()
    inv_path.write_text(json.dumps(committed, indent=2, sort_keys=True), encoding="utf-8")
    full = _minimal_full_inventory()
    full["files"][0]["likely_architecture_layer"] = "engine"
    monkeypatch.setattr(audit_mod, "GOVERNANCE_JSON", inv_path)
    monkeypatch.setattr(audit_mod, "build_inventory_payload", lambda: full)
    assert audit_mod.run_inventory_check() == 1


def test_run_inventory_check_fails_when_registry_path_missing(audit_mod, tmp_path: Path, monkeypatch) -> None:
    inv_path = tmp_path / "test_inventory_governance.json"
    full = _minimal_full_inventory()
    gov = audit_mod.build_governance_payload(full)
    gov["files"] = []
    inv_path.write_text(json.dumps(gov, indent=2, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(audit_mod, "GOVERNANCE_JSON", inv_path)
    monkeypatch.setattr(audit_mod, "build_inventory_payload", lambda: full)
    assert audit_mod.run_inventory_check() == 1


def test_architecture_layer_gauntlet_regressions_beats_call_gpt_patch(audit_mod) -> None:
    fp = "tests/test_gauntlet_regressions.py"
    src = 'm.setattr("game.api.call_gpt", lambda _messages: {"player_facing_text": "x"})\n'
    scores = audit_mod._architecture_layer_scores(fp, src, "regression")
    assert audit_mod._primary_architecture_layer(scores) == "gauntlet"


def test_architecture_layer_narrative_mode_validator_is_gpt(audit_mod) -> None:
    fp = "tests/test_narrative_mode_output_validator.py"
    src = "from game.narrative_mode_contract import validate_narrative_mode_output\n"
    scores = audit_mod._architecture_layer_scores(fp, src, "mixed/unclear")
    assert audit_mod._primary_architecture_layer(scores) == "gpt"


def test_main_check_dispatches_without_writing(audit_mod, tmp_path: Path, monkeypatch) -> None:
    inv_path = tmp_path / "test_inventory_governance.json"
    full = _minimal_full_inventory()
    gov = audit_mod.build_governance_payload(full)
    inv_path.write_text(json.dumps(gov, indent=2, sort_keys=True), encoding="utf-8")
    monkeypatch.setattr(audit_mod, "GOVERNANCE_JSON", inv_path)
    monkeypatch.setattr(
        audit_mod,
        "build_inventory_payload",
        lambda: _minimal_full_inventory(generated_utc="2026-06-04T00:00:00+00:00"),
    )
    assert audit_mod.main(["--check"]) == 0
    assert inv_path.read_text(encoding="utf-8") == json.dumps(gov, indent=2, sort_keys=True)


def test_build_governance_payload_strips_diagnostic_fields(audit_mod) -> None:
    full = _minimal_full_inventory()
    full["ownership_registry_index"] = {"available": True, "groups": {}, "files_roles": {}}
    gov = audit_mod.build_governance_payload(full)
    assert gov["summary"]["inventory_kind"] == "governance"
    assert len(gov["files"]) == 1
    assert gov["files"][0]["path"] == GOVERNANCE_FIXTURE_PATH
    assert "collected_nodeids" not in gov["files"][0]
    assert "overlap_hints" not in gov["files"][0]
    assert "tests" not in gov
    assert "block_b_overlap_clusters" not in gov
    assert "import_hub_modules" not in gov
    assert "ownership_registry_index" not in gov
    assert "ownership_registry_positions" not in gov["files"][0]
    for key in audit_mod.GOVERNANCE_FILE_FIELDS:
        assert key in gov["files"][0]
    assert set(gov.keys()) == {
        "summary",
        "files",
    }
    assert set(gov["summary"]) == set(audit_mod.GOVERNANCE_SUMMARY_FIELDS)


def test_validate_governance_summary_shape_rejects_derivable_fields(audit_mod) -> None:
    gov = _minimal_inventory()
    gov["summary"]["test_file_count"] = 99
    assert audit_mod._validate_governance_summary_shape(gov)


def test_validate_derived_cross_file_duplicate_governance_uses_allowlist(audit_mod) -> None:
    full = _minimal_full_inventory()
    full["cross_file_duplicate_test_names"] = [{"base_name": "test_unlisted_dup", "files": ["tests/test_a.py"]}]
    errors = audit_mod._validate_derived_cross_file_duplicate_governance(full)
    assert errors
    full["cross_file_duplicate_test_names"] = []
    assert not audit_mod._validate_derived_cross_file_duplicate_governance(full)


def test_governance_payload_excludes_non_registry_files(audit_mod) -> None:
    full = _minimal_full_inventory()
    gov = audit_mod.build_governance_payload(full)
    committed_paths = {row["path"] for row in gov["files"]}
    assert NON_REGISTRY_FIXTURE_PATH not in committed_paths
    assert GOVERNANCE_FIXTURE_PATH in committed_paths
    assert audit_mod.governance_committed_file_paths(full) >= committed_paths


def test_validate_full_diagnostic_triage_aggregates(audit_mod) -> None:
    full = _minimal_full_inventory()
    assert not audit_mod._validate_full_diagnostic_triage_aggregates(full)
    broken = _minimal_full_inventory()
    broken.pop("block_b_overlap_clusters", None)
    assert audit_mod._validate_full_diagnostic_triage_aggregates(broken)


def test_derive_per_test_marker_rows_from_full_payload(audit_mod) -> None:
    full = _minimal_full_inventory()
    rows = audit_mod.derive_per_test_marker_rows(full)
    assert len(rows) == 2
    assert rows[0]["nodeid"] == f"{GOVERNANCE_FIXTURE_PATH}::test_ok"
    assert rows[0]["marker_set"] == ["unit"]


def test_validate_governance_committed_file_paths_detects_missing_registry_path(audit_mod) -> None:
    full = _minimal_full_inventory()
    gov = audit_mod.build_governance_payload(full)
    gov["files"] = []
    errors = audit_mod._validate_governance_committed_file_paths(full, gov)
    assert any("missing registry-owned paths" in e or "missing required paths" in e for e in errors)


def test_validate_derived_marker_governance_detects_file_union_mismatch(audit_mod) -> None:
    full = _minimal_full_inventory()
    full["files"][0]["marker_set"] = ["integration"]
    errors = audit_mod._validate_derived_marker_governance(full)
    assert any("files[].marker_set" in e for e in errors)


def test_write_full_inventory_writes_diagnostic_payload(audit_mod, tmp_path: Path) -> None:
    out = tmp_path / "full.json"
    full = _minimal_full_inventory()
    audit_mod.write_full_inventory(full, out)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["summary"]["inventory_kind"] == "full"
    assert "collected_nodeids" in loaded["files"][0]
    assert "brittleness" in loaded["tests"][0]
    assert "block_b_overlap_clusters" in loaded
    assert "import_hub_modules" in loaded


def test_main_full_flag_writes_diagnostic_file(audit_mod, tmp_path: Path, monkeypatch) -> None:
    gov_path = tmp_path / "gov.json"
    full_path = tmp_path / "full.json"
    monkeypatch.setattr(audit_mod, "GOVERNANCE_JSON", gov_path)
    monkeypatch.setattr(audit_mod, "FULL_INVENTORY_DEFAULT", full_path)
    monkeypatch.setattr(audit_mod, "build_inventory_payload", lambda: _minimal_full_inventory())
    assert audit_mod.main(["--full"]) == 0
    assert gov_path.is_file()
    assert full_path.is_file()
    assert "collected_nodeids" in json.loads(full_path.read_text(encoding="utf-8"))["files"][0]
