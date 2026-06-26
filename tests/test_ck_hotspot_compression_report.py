"""CK-GIT hotspot compression report validation."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from tests.helpers.ck_hotspot_compression_report import (
    DEFAULT_BU_CSV_PATH,
    T_TOUCH,
    aggregate_touches_from_commit_paths,
    assess_measurement_readiness,
    compute_ck_git_metrics,
    compute_concentration_shares,
    is_ck_git_population_path,
    parse_ck_fi_metrics,
    rank_hotspots,
    write_ck_hotspot_compression_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
BU_CSV = REPO_ROOT / DEFAULT_BU_CSV_PATH


def _synthetic_commit_paths() -> list[list[str]]:
    return [
        ["game/a.py", "tests/b.py", "docs/audits/x.py", "artifacts/y.py"],
        ["tests/b.py", "tests/c.py"],
        ["tests/c.py", "game/a.py", "scripts/d.py"],
        ["game/e.py"],
        ["tests/f.py", "tests/g.py"],
    ]


def test_population_path_filters():
    assert is_ck_git_population_path("game/foo.py")
    assert is_ck_git_population_path("tests/helpers/x.py")
    assert is_ck_git_population_path("scripts/run.py")
    assert not is_ck_git_population_path("docs/audits/foo.py")
    assert not is_ck_git_population_path("artifacts/foo.py")
    assert not is_ck_git_population_path("game/foo.bak")
    assert not is_ck_git_population_path("README.md")


def test_hci_and_concentration_calculation():
    touches = aggregate_touches_from_commit_paths(_synthetic_commit_paths())
    metrics = compute_ck_git_metrics(touches)

    assert touches["game/a.py"] == 2
    assert touches["tests/b.py"] == 2
    assert touches["tests/c.py"] == 2
    assert metrics["total_touches"] == 10
    assert metrics["hci"] == metrics["top5_share_pct"]
    assert metrics["top5_share_pct"] == 80.0
    assert metrics["top10_share_pct"] == 100.0
    assert metrics["files_above_threshold"] == 0


def test_hotspot_ranking_and_tie_breaking():
    touches = Counter(
        {
            "tests/z_last.py": 3,
            "tests/a_first.py": 3,
            "game/middle.py": 2,
        }
    )
    ranked = rank_hotspots(touches)

    assert [entry.path for entry in ranked] == [
        "tests/a_first.py",
        "tests/z_last.py",
        "game/middle.py",
    ]
    assert ranked[0].touch_count == 3
    assert ranked[1].touch_count == 3


def test_threshold_population():
    touches = Counter(
        {
            "game/hot.py": 4,
            "tests/warm.py": 3,
            "scripts/cool.py": 2,
        }
    )
    metrics = compute_ck_git_metrics(touches)

    assert metrics["files_above_threshold"] == 2
    assert metrics["t_touch"] == T_TOUCH


def test_concentration_empty_window():
    ranked = rank_hotspots({})
    assert compute_concentration_shares(ranked, total_touches=0, top_n=5) == 0.0
    metrics = compute_ck_git_metrics(Counter())
    assert metrics["hci"] == 0.0
    assert metrics["largest_hotspot"] is None


def test_measurement_readiness_states():
    assert (
        assess_measurement_readiness(
            total_touches=0,
            commit_count=0,
            watch_start="abc",
            measurement_commit="abc",
        )
        == "empty_window"
    )
    assert (
        assess_measurement_readiness(
            total_touches=0,
            commit_count=3,
            watch_start="abc",
            measurement_commit="def",
        )
        == "insufficient_data"
    )
    assert (
        assess_measurement_readiness(
            total_touches=10,
            commit_count=3,
            watch_start="abc",
            measurement_commit="def",
        )
        == "measurement_ready"
    )


def test_ck_fi_parse_from_bu_csv():
    if not BU_CSV.is_file():
        pytest.skip("BU CSV not present")
    fi = parse_ck_fi_metrics(BU_CSV, repo_root=REPO_ROOT)
    assert fi["available"] is True
    assert fi["top5_share_pct"] == pytest.approx(20.79, abs=0.01)
    assert fi["top10_share_pct"] == pytest.approx(32.76, abs=0.01)
    assert fi["files_above_threshold"] == 39
    assert "FI top5=" in fi["notes_string"]


def test_report_generation_synthetic_fixture(tmp_path):
    output_md = tmp_path / "ck1_hotspot_compression_report.md"
    output_json = tmp_path / "ck1_hotspot_compression_report.json"

    report, markdown = write_ck_hotspot_compression_report(
        md_output_path=output_md,
        json_output_path=output_json,
        bu_csv_path=BU_CSV,
        commit_paths=_synthetic_commit_paths(),
        commit_count=5,
        watch_start_full="aaa00000000000000000000000000000000000000",
        watch_start_short="aaa0000",
        measurement_full="bbb00000000000000000000000000000000000000",
        measurement_short="bbb0000",
        measurement_date="2026-06-26",
        repo_root=REPO_ROOT,
    )

    assert output_md.exists()
    assert output_json.exists()
    assert report["generation_status"] == "success"
    assert report["ck_git"]["hci"] == 80.0
    assert report["measurement_readiness"] == "measurement_ready"
    assert "Hotspot Rankings" in markdown

    payload = json.loads(output_json.read_text(encoding="utf-8"))
    assert payload["ck_git"]["top10_share_pct"] == 100.0
    assert len(payload["ck_git"]["hotspot_rankings"]) == 7


@pytest.mark.skipif(not (REPO_ROOT / ".git").is_dir(), reason="requires git repository")
def test_report_generation_validation_window(tmp_path):
    """Validation window from CI_2/CI_4 — not for CK log insertion."""
    output_json = tmp_path / "ck1_validation.json"
    report, _ = write_ck_hotspot_compression_report(
        json_output_path=output_json,
        md_output_path=tmp_path / "ck1_validation.md",
        watch_start="5f0ad53",
        measurement_commit="85855df",
        bu_csv_path=BU_CSV,
        repo_root=REPO_ROOT,
    )
    ck_git = report["ck_git"]
    assert ck_git["total_touches"] == 105
    assert ck_git["top5_share_pct"] == pytest.approx(9.52, abs=0.01)
    assert ck_git["top10_share_pct"] == pytest.approx(18.10, abs=0.01)
    assert ck_git["files_above_threshold"] == 0
    assert ck_git["largest_hotspot"]["path"] == "tests/helpers/failure_dashboard_recurrence.py"


@pytest.mark.skipif(not (REPO_ROOT / ".git").is_dir(), reason="requires git repository")
def test_report_generation_empty_watch_window(tmp_path):
    output_json = tmp_path / "ck1_empty.json"
    report, _ = write_ck_hotspot_compression_report(
        json_output_path=output_json,
        md_output_path=tmp_path / "ck1_empty.md",
        watch_start="85855df",
        measurement_commit="85855df",
        bu_csv_path=BU_CSV,
        repo_root=REPO_ROOT,
    )
    assert report["measurement_readiness"] == "empty_window"
    assert report["data_sufficient"] is False
    assert report["ck_git"]["total_touches"] == 0
    assert report["ck_git"]["hci"] == 0.0
