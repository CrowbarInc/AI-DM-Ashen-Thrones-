"""CA2 corrective-change locality path classifier validation."""
from __future__ import annotations

import pytest

from tests.helpers.corrective_change_locality_classifier import (
    PATH_BUCKETS,
    classify_path,
    classify_paths,
    validate_classification,
)


@pytest.mark.parametrize(
    ("path", "expected_bucket"),
    [
        ("game/api.py", "production_runtime_source"),
        ("static/app.js", "production_runtime_source"),
        ("tests/test_start_campaign_api.py", "tests"),
        ("tests/helpers/golden_replay.py", "tests"),
        ("docs/reports/openai_api_key_lazy_config_fix_20260520.md", "docs_reports"),
        ("audits/cycle_f_final_gate_hotspot_touch_budget_20260518.md", "docs_reports"),
        ("README.md", "docs_reports"),
        ("tools/bug_fix_locality_report.py", "scripts_tools"),
        ("scripts/bu4_ownership_write_path_discovery.py", "scripts_tools"),
        (".github/workflows/convergence-checks.yml", "scripts_tools"),
        ("pyproject.toml", "scripts_tools"),
        ("data/session.json", "fixtures_data"),
        ("data/scenes/frontier_gate.json", "fixtures_data"),
        ("artifacts/bug_fix_locality_report.md", "generated_artifacts"),
        (
            "codex_pytest_tmp19/test_start_campaign_emits_open0/data/session.json",
            "generated_artifacts",
        ),
        ("unknown.xyz", "unclassified"),
    ],
)
def test_representative_path_classification(path: str, expected_bucket: str) -> None:
    assert classify_path(path) == expected_bucket


def test_codex_pytest_tmp_isolated_from_tests_bucket() -> None:
    path = "codex_pytest_tmp30/test_public_log_exposes_player0/data/session.json"
    assert classify_path(path) == "generated_artifacts"
    assert classify_path(path) != "tests"


def test_classify_paths_reconciles_bucket_totals() -> None:
    paths = [
        "game/api.py",
        "tests/test_api.py",
        "docs/reports/foo.md",
        "tools/foo.py",
        "data/session.json",
        "artifacts/report.md",
        "codex_pytest_tmp1/run/data/session.json",
    ]
    summary = classify_paths(paths)
    assert validate_classification(summary) == []
    assert summary.total_paths == len(paths)
    assert sum(summary.bucket_counts.values()) == len(paths)


def test_classify_paths_rejects_unknown_bucket(monkeypatch) -> None:
    def _bad_bucket(_path: str) -> str:
        return "not_a_real_bucket"

    monkeypatch.setattr(
        "tests.helpers.corrective_change_locality_classifier.classify_path",
        _bad_bucket,
    )
    with pytest.raises(ValueError, match="unknown bucket"):
        classify_paths(["game/api.py"])


def test_duplicate_path_assignment_is_detected() -> None:
    summary = classify_paths(["game/api.py", "game/api.py"])
    assert any("duplicate bucket assignment" in err for err in validate_classification(summary))


def test_all_buckets_are_known() -> None:
    for bucket in PATH_BUCKETS:
        assert bucket in PATH_BUCKETS
