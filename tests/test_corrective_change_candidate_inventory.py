"""CA5 corrective-change candidate inventory validation."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.helpers.corrective_change_candidate_inventory import (
    CandidateCommit,
    ReviewQueueRow,
    deduplicate_candidates,
    normalize_keywords,
    sort_candidates,
    subject_matches_keywords,
    validate_unique_commit_hashes,
)
from tools.corrective_change_candidate_inventory import (
    build_candidate_inventory_payload,
    generate_review_queue_rows,
    load_frozen_cohort_hashes,
    load_intake_since_date,
    render_candidate_inventory_md,
    write_corrective_change_candidate_inventory,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
COHORT_CSV = REPO_ROOT / "docs" / "audits" / "CA_corrective_change_locality_cohort.csv"
BASELINE_JSON = REPO_ROOT / "docs" / "baselines" / "ca_corrective_locality_baseline.json"
REVIEW_QUEUE_CSV = REPO_ROOT / "docs" / "audits" / "ca_review_queue.csv"


def _candidate(
    commit_hash: str,
    *,
    date: str = "2026-06-22",
    subject: str = "Preserve replay routing fallback guard",
) -> CandidateCommit:
    return CandidateCommit(
        commit_hash=commit_hash,
        date=date,
        subject=subject,
        files_touched=7,
        production_files_touched=2,
        test_files_touched=1,
        generated_files_touched=0,
        matched_keywords=("preserve", "replay", "routing", "fallback", "guard"),
    )


def test_default_keyword_list_is_configurable():
    defaults = normalize_keywords(None)
    custom = normalize_keywords(["fix", "repair"])
    assert "fix" in defaults
    assert "mutation" in defaults
    assert custom == ("fix", "repair")
    with pytest.raises(ValueError, match="keyword list must not be empty"):
        normalize_keywords(["", "  "])


def test_subject_keyword_matching():
    assert subject_matches_keywords("Preserve replay routing fallback", normalize_keywords(None))
    assert not subject_matches_keywords("Cycle BI ownership isolation", normalize_keywords(None))


def test_duplicate_prevention():
    candidates = [
        _candidate("abc123"),
        _candidate("abc123", date="2026-06-21"),
    ]
    unique = deduplicate_candidates(candidates)
    assert len(unique) == 1
    assert validate_unique_commit_hashes(unique) == []
    assert validate_unique_commit_hashes(candidates) != []


def test_candidate_sorting():
    candidates = [
        _candidate("bbbbbbb", date="2026-06-20"),
        _candidate("aaaaaaa", date="2026-06-22"),
        _candidate("ccccccc", date="2026-06-22"),
    ]
    sorted_candidates = sort_candidates(candidates)
    assert [row.commit_hash for row in sorted_candidates] == ["aaaaaaa", "ccccccc", "bbbbbbb"]


def test_review_queue_generation_merges_without_duplicates():
    candidates = [
        _candidate("1111111"),
        _candidate("2222222"),
    ]
    existing = [
        ReviewQueueRow(
            commit_hash="1111111",
            reviewed=True,
            qualifies="true",
            confidence="high",
            defect_statement="already reviewed",
            repair_family="routing",
            notes="manual",
        )
    ]
    merged = generate_review_queue_rows(candidates, existing)
    assert len(merged) == 2
    preserved = next(row for row in merged if row.commit_hash == "1111111")
    added = next(row for row in merged if row.commit_hash == "2222222")
    assert preserved.reviewed is True
    assert preserved.notes == "manual"
    assert added.reviewed is False
    assert "auto-discovered" in added.notes


def test_inventory_payload_structure():
    candidates = sort_candidates([_candidate("abc123"), _candidate("def456")])
    payload = build_candidate_inventory_payload(
        candidates,
        keywords=normalize_keywords(None),
        since_date="2026-05-20",
        excluded_hash_count=11,
    )
    assert payload["candidate_count"] == 2
    assert payload["since_date"] == "2026-05-20"
    assert payload["candidates"][0]["commit_hash"] == "abc123"
    markdown = render_candidate_inventory_md(payload)
    assert "Qualification checklist" in markdown
    assert "Exclusion checklist" in markdown


def test_frozen_cohort_hashes_exclude_baseline_commits():
    frozen = load_frozen_cohort_hashes(COHORT_CSV, repo_root=REPO_ROOT)
    assert len(frozen) == 11
    assert "6a402d264eec1bd4ef5be98407998ba105e30f52" in frozen


def test_intake_since_date_comes_from_baseline():
    since_date = load_intake_since_date(BASELINE_JSON, repo_root=REPO_ROOT)
    assert since_date == "2026-05-20"


def test_inventory_generation_integration(tmp_path):
    inventory_json = tmp_path / "ca5_candidate_inventory.json"
    inventory_md = tmp_path / "ca5_candidate_inventory.md"
    intake_report = tmp_path / "ca5_intake_pipeline_report.md"
    review_queue = tmp_path / "ca_review_queue.csv"
    review_queue.write_text("commit_hash,reviewed,qualifies,confidence,defect_statement,repair_family,notes\n", encoding="utf-8")

    inventory, report, queue = write_corrective_change_candidate_inventory(
        inventory_json_path=inventory_json,
        inventory_md_path=inventory_md,
        intake_report_path=intake_report,
        review_queue_path=review_queue,
        cohort_csv_path=COHORT_CSV,
        baseline_json_path=BASELINE_JSON,
        repo_root=REPO_ROOT,
    )

    assert inventory_json.exists()
    assert inventory_md.exists()
    assert intake_report.exists()
    assert review_queue.exists()
    assert inventory["candidate_count"] > 0
    assert report["validation_status"] == "PASS"
    assert len(queue) == inventory["candidate_count"]

    loaded = json.loads(inventory_json.read_text(encoding="utf-8"))
    hashes = [row["commit_hash"] for row in loaded["candidates"]]
    assert len(hashes) == len(set(hashes))
    frozen = load_frozen_cohort_hashes(COHORT_CSV, repo_root=REPO_ROOT)
    assert frozen.isdisjoint(hashes)
