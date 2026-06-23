#!/usr/bin/env python3
"""CA5 corrective-change candidate intake inventory generator.

Discovers keyword-nominated commits from git history, classifies touched paths
with CA2 accounting, and seeds the human review queue for future cohort assembly.
Read-side only: no baseline changes, trend comparison, or cohort mutation.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.corrective_change_candidate_inventory import (  # noqa: E402
    EXCLUSION_CHECKLIST,
    QUALIFICATION_CHECKLIST,
    REVIEW_QUEUE_FIELDS,
    CandidateCommit,
    ReviewQueueRow,
    deduplicate_candidates,
    matched_keywords_for_subject,
    normalize_keywords,
    sort_candidates,
    subject_matches_keywords,
    validate_unique_commit_hashes,
)
from tests.helpers.corrective_locality_baseline import (  # noqa: E402
    DEFAULT_BASELINE_JSON_PATH,
    load_baseline,
)
from tests.helpers.corrective_change_locality_cohort import (  # noqa: E402
    DEFAULT_COHORT_CSV_PATH,
    load_cohort,
)
from tools.corrective_change_locality import (  # noqa: E402
    collect_changed_paths,
    compute_locality_counts,
)

DEFAULT_INVENTORY_JSON_PATH = "artifacts/ca5_candidate_inventory.json"
DEFAULT_INVENTORY_MD_PATH = "artifacts/ca5_candidate_inventory.md"
DEFAULT_INTAKE_REPORT_PATH = "artifacts/ca5_intake_pipeline_report.md"
DEFAULT_REVIEW_QUEUE_PATH = "docs/audits/ca_review_queue.csv"
INVENTORY_SCHEMA_VERSION = 1


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root if repo_root is not None else ROOT


def load_frozen_cohort_hashes(
    csv_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> set[str]:
    """Return commit hashes from the frozen CA1 cohort authority CSV."""
    target = Path(csv_path or DEFAULT_COHORT_CSV_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    return {row.commit_hash for row in load_cohort(target) if row.commit_hash}


def load_intake_since_date(
    baseline_path: str | Path | None = None,
    *,
    since_date: str | None = None,
    repo_root: Path | None = None,
) -> str:
    """Return the default intake start date from CA4 baseline boundaries."""
    if since_date:
        return since_date
    target = Path(baseline_path or DEFAULT_BASELINE_JSON_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    baseline = load_baseline(target)
    boundaries = baseline.get("cohort_boundaries") or {}
    return str(boundaries.get("end_date") or "")


def git_list_commits(
    *,
    repo_root: Path | None = None,
    since_date: str | None = None,
) -> list[dict[str, str]]:
    """List non-merge commits from git log as hash/date/subject records."""
    root = _repo_root(repo_root)
    command = ["git", "log", "--format=%H|%ad|%s", "--date=short", "--no-merges"]
    if since_date:
        command.append(f"--since={since_date}")
    result = subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise ValueError(f"git log failed: {stderr or result.returncode}")

    commits: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        commit_hash, date, subject = line.split("|", 2)
        commits.append(
            {
                "commit_hash": commit_hash.strip(),
                "date": date.strip(),
                "subject": subject.strip(),
            }
        )
    return commits


def count_commit_paths(commit_hash: str, *, repo_root: Path | None = None) -> dict[str, int]:
    """Collect CA2 bucket counts for one commit."""
    paths = collect_changed_paths(commit_hash, repo_root=repo_root)
    summary = compute_locality_counts(paths)
    counts = summary.bucket_counts
    return {
        "files_touched": summary.total_paths,
        "production_files_touched": counts.get("production_runtime_source", 0),
        "test_files_touched": counts.get("tests", 0),
        "generated_files_touched": counts.get("generated_artifacts", 0),
    }


def discover_candidates(
    *,
    keywords: Sequence[str] | None = None,
    since_date: str | None = None,
    exclude_hashes: set[str] | None = None,
    repo_root: Path | None = None,
    include_counts: bool = True,
) -> list[CandidateCommit]:
    """Discover keyword-nominated commits after intake boundaries, excluding frozen cohort hashes."""
    normalized_keywords = normalize_keywords(keywords)
    excluded = set(exclude_hashes or ())
    candidates: list[CandidateCommit] = []

    for commit in git_list_commits(repo_root=repo_root, since_date=since_date):
        commit_hash = commit["commit_hash"]
        if since_date and commit["date"] <= since_date:
            continue
        if commit_hash in excluded:
            continue
        subject = commit["subject"]
        if not subject_matches_keywords(subject, normalized_keywords):
            continue

        if include_counts:
            try:
                counts = count_commit_paths(commit_hash, repo_root=repo_root)
            except ValueError:
                continue
        else:
            counts = {
                "files_touched": 0,
                "production_files_touched": 0,
                "test_files_touched": 0,
                "generated_files_touched": 0,
            }

        candidates.append(
            CandidateCommit(
                commit_hash=commit_hash,
                date=commit["date"],
                subject=subject,
                files_touched=counts["files_touched"],
                production_files_touched=counts["production_files_touched"],
                test_files_touched=counts["test_files_touched"],
                generated_files_touched=counts["generated_files_touched"],
                matched_keywords=matched_keywords_for_subject(subject, normalized_keywords),
            )
        )

    unique = deduplicate_candidates(candidates)
    duplicate_errors = validate_unique_commit_hashes(unique)
    if duplicate_errors:
        raise ValueError(duplicate_errors[0])
    return sort_candidates(unique)


def build_candidate_inventory_payload(
    candidates: Sequence[CandidateCommit],
    *,
    keywords: Sequence[str],
    since_date: str,
    excluded_hash_count: int,
) -> dict[str, Any]:
    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "primary_metric": "files_touched_per_fix",
        "discovery_keywords": list(keywords),
        "since_date": since_date,
        "excluded_frozen_cohort_hashes": excluded_hash_count,
        "candidate_count": len(candidates),
        "candidates": [asdict(candidate) for candidate in candidates],
    }


def render_candidate_inventory_md(
    payload: Mapping[str, Any],
) -> str:
    lines = [
        "# CA5 Corrective Change Candidate Inventory",
        "",
        "> Keyword-nominated commits awaiting human corrective-fix review.",
        "",
        f"_Since date: **{payload.get('since_date')}** — candidates: **{payload.get('candidate_count')}**._",
        "",
        "## Candidate table",
        "",
        "| Date | Commit | Subject | Files | Production | Tests | Generated | Keywords |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ]
    for candidate in payload.get("candidates") or []:
        keywords = ", ".join(candidate.get("matched_keywords") or [])
        subject = str(candidate.get("subject") or "").replace("|", "\\|")
        commit_hash = str(candidate.get("commit_hash") or "")
        lines.append(
            f"| {candidate.get('date')} | `{commit_hash[:7]}` | {subject} | "
            f"{candidate.get('files_touched')} | {candidate.get('production_files_touched')} | "
            f"{candidate.get('test_files_touched')} | {candidate.get('generated_files_touched')} | {keywords} |"
        )

    lines.extend(["", "## Qualification checklist", ""])
    for item in QUALIFICATION_CHECKLIST:
        lines.append(f"- [ ] {item}")

    lines.extend(["", "## Exclusion checklist", ""])
    for item in EXCLUSION_CHECKLIST:
        lines.append(f"- [ ] {item}")
    lines.append("")
    return "\n".join(lines)


def load_review_queue(path: str | Path | None = None, *, repo_root: Path | None = None) -> list[ReviewQueueRow]:
    target = Path(path or DEFAULT_REVIEW_QUEUE_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    if not target.is_file():
        return []

    rows: list[ReviewQueueRow] = []
    with target.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return rows
        for raw in reader:
            commit_hash = str(raw.get("commit_hash") or "").strip()
            if not commit_hash:
                continue
            reviewed_text = str(raw.get("reviewed") or "").strip().lower()
            rows.append(
                ReviewQueueRow(
                    commit_hash=commit_hash,
                    reviewed=reviewed_text in {"true", "1", "yes"},
                    qualifies=str(raw.get("qualifies") or "").strip(),
                    confidence=str(raw.get("confidence") or "").strip(),
                    defect_statement=str(raw.get("defect_statement") or "").strip(),
                    repair_family=str(raw.get("repair_family") or "").strip(),
                    notes=str(raw.get("notes") or "").strip(),
                )
            )
    return rows


def generate_review_queue_rows(
    candidates: Sequence[CandidateCommit],
    existing_rows: Sequence[ReviewQueueRow],
) -> list[ReviewQueueRow]:
    """Merge discovered candidates into the review queue without duplicating commit hashes."""
    by_hash = {row.commit_hash: row for row in existing_rows}
    merged: list[ReviewQueueRow] = list(existing_rows)

    for candidate in candidates:
        if candidate.commit_hash in by_hash:
            continue
        row = ReviewQueueRow(
            commit_hash=candidate.commit_hash,
            reviewed=False,
            qualifies="",
            confidence="",
            defect_statement="",
            repair_family="",
            notes=f"auto-discovered {candidate.date}; keywords={','.join(candidate.matched_keywords)}",
        )
        by_hash[candidate.commit_hash] = row
        merged.append(row)

    duplicate_hashes = validate_unique_commit_hashes(
        [CandidateCommit(commit_hash=row.commit_hash, date="", subject="", files_touched=0,
                         production_files_touched=0, test_files_touched=0,
                         generated_files_touched=0, matched_keywords=()) for row in merged]
    )
    if duplicate_hashes:
        raise ValueError(duplicate_hashes[0])

    return sorted(merged, key=lambda row: row.commit_hash)


def write_review_queue_csv(
    rows: Sequence[ReviewQueueRow],
    output_path: str | Path | None = None,
    *,
    repo_root: Path | None = None,
) -> None:
    target = Path(output_path or DEFAULT_REVIEW_QUEUE_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REVIEW_QUEUE_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "commit_hash": row.commit_hash,
                    "reviewed": "true" if row.reviewed else "false",
                    "qualifies": row.qualifies,
                    "confidence": row.confidence,
                    "defect_statement": row.defect_statement,
                    "repair_family": row.repair_family,
                    "notes": row.notes,
                }
            )


def build_intake_pipeline_report(
    *,
    inventory: Mapping[str, Any],
    review_queue_rows: Sequence[ReviewQueueRow],
    validation_errors: Sequence[str],
) -> dict[str, Any]:
    reviewed_count = sum(1 for row in review_queue_rows if row.reviewed)
    pending_count = len(review_queue_rows) - reviewed_count
    return {
        "schema_version": INVENTORY_SCHEMA_VERSION,
        "inventory_candidate_count": inventory.get("candidate_count", 0),
        "review_queue_total": len(review_queue_rows),
        "review_queue_reviewed": reviewed_count,
        "review_queue_pending": pending_count,
        "validation_status": "PASS" if not validation_errors else "FAIL",
        "validation_errors": list(validation_errors),
    }


def render_intake_pipeline_report_md(report: Mapping[str, Any], inventory: Mapping[str, Any]) -> str:
    lines = [
        "# CA5 Corrective Change Intake Pipeline Report",
        "",
        "> CA5 candidate discovery and review-queue intake for future corrective cohort assembly.",
        "",
        "## Inventory statistics",
        "",
        f"- **Since date:** {inventory.get('since_date')}",
        f"- **Discovery keywords:** {', '.join(inventory.get('discovery_keywords') or [])}",
        f"- **Excluded frozen cohort hashes:** {inventory.get('excluded_frozen_cohort_hashes')}",
        f"- **Candidate count:** {inventory.get('candidate_count')}",
        "",
        "## Queue statistics",
        "",
        f"- **Review queue total:** {report.get('review_queue_total')}",
        f"- **Reviewed rows:** {report.get('review_queue_reviewed')}",
        f"- **Pending review rows:** {report.get('review_queue_pending')}",
        "",
        "## Validation results",
        "",
        f"- **Status:** {report.get('validation_status')}",
    ]
    errors = report.get("validation_errors") or []
    if errors:
        for error in errors:
            lines.append(f"- FAIL: {error}")
    else:
        lines.append("- PASS: candidate inventory generated")
        lines.append("- PASS: duplicate commit hashes prevented")
        lines.append("- PASS: candidates sorted deterministically")
        lines.append("- PASS: review queue merged without duplicates")
    lines.append("")
    return "\n".join(lines)


def write_corrective_change_candidate_inventory(
    *,
    inventory_json_path: str | Path | None = None,
    inventory_md_path: str | Path | None = None,
    intake_report_path: str | Path | None = None,
    review_queue_path: str | Path | None = None,
    cohort_csv_path: str | Path | None = None,
    baseline_json_path: str | Path | None = None,
    since_date: str | None = None,
    keywords: Sequence[str] | None = None,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], list[ReviewQueueRow]]:
    """Generate CA5 inventory artifacts and merge the review queue."""
    root = _repo_root(repo_root)
    normalized_keywords = normalize_keywords(keywords)
    frozen_hashes = load_frozen_cohort_hashes(cohort_csv_path, repo_root=root)
    intake_since = load_intake_since_date(
        baseline_json_path,
        since_date=since_date,
        repo_root=root,
    )
    if not intake_since:
        raise ValueError("intake since_date could not be determined")

    candidates = discover_candidates(
        keywords=normalized_keywords,
        since_date=intake_since,
        exclude_hashes=frozen_hashes,
        repo_root=root,
    )
    inventory = build_candidate_inventory_payload(
        candidates,
        keywords=normalized_keywords,
        since_date=intake_since,
        excluded_hash_count=len(frozen_hashes),
    )

    existing_queue = load_review_queue(review_queue_path, repo_root=root)
    review_queue_rows = generate_review_queue_rows(candidates, existing_queue)

    validation_errors: list[str] = []
    validation_errors.extend(validate_unique_commit_hashes(candidates))
    if len({row.commit_hash for row in review_queue_rows}) != len(review_queue_rows):
        validation_errors.append("review queue contains duplicate commit hashes")
    if validation_errors:
        raise ValueError(
            "CA5 intake validation failed:\n" + "\n".join(f"- {err}" for err in validation_errors)
        )

    inventory_json_target = Path(inventory_json_path or DEFAULT_INVENTORY_JSON_PATH)
    inventory_md_target = Path(inventory_md_path or DEFAULT_INVENTORY_MD_PATH)
    intake_report_target = Path(intake_report_path or DEFAULT_INTAKE_REPORT_PATH)
    for target in (inventory_json_target, inventory_md_target, intake_report_target):
        if not target.is_absolute():
            target = root / target
        target.parent.mkdir(parents=True, exist_ok=True)

    inventory_json_target.write_text(
        json.dumps(inventory, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    inventory_md_target.write_text(render_candidate_inventory_md(inventory), encoding="utf-8")
    write_review_queue_csv(review_queue_rows, review_queue_path, repo_root=root)

    intake_report = build_intake_pipeline_report(
        inventory=inventory,
        review_queue_rows=review_queue_rows,
        validation_errors=validation_errors,
    )
    if not intake_report_target.is_absolute():
        intake_report_target = root / intake_report_target
    intake_report_target.write_text(
        render_intake_pipeline_report_md(intake_report, inventory),
        encoding="utf-8",
    )
    return inventory, intake_report, review_queue_rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate CA5 corrective-change candidate inventory and review queue.",
    )
    parser.add_argument(
        "--since-date",
        default=None,
        help="Intake start date (YYYY-MM-DD). Defaults to CA4 baseline end date.",
    )
    parser.add_argument(
        "--keyword",
        action="append",
        dest="keywords",
        help="Discovery keyword (repeatable). Defaults to CA5 standard keyword list.",
    )
    parser.add_argument(
        "--inventory-json",
        type=Path,
        default=ROOT / DEFAULT_INVENTORY_JSON_PATH,
    )
    parser.add_argument(
        "--inventory-md",
        type=Path,
        default=ROOT / DEFAULT_INVENTORY_MD_PATH,
    )
    parser.add_argument(
        "--intake-report",
        type=Path,
        default=ROOT / DEFAULT_INTAKE_REPORT_PATH,
    )
    parser.add_argument(
        "--review-queue",
        type=Path,
        default=ROOT / DEFAULT_REVIEW_QUEUE_PATH,
    )
    args = parser.parse_args()

    inventory, report, queue = write_corrective_change_candidate_inventory(
        inventory_json_path=args.inventory_json,
        inventory_md_path=args.inventory_md,
        intake_report_path=args.intake_report,
        review_queue_path=args.review_queue,
        since_date=args.since_date,
        keywords=args.keywords,
        repo_root=ROOT,
    )
    print(
        f"Wrote {args.inventory_json} ({inventory['candidate_count']} candidates), "
        f"{args.review_queue} ({len(queue)} queue rows), {args.intake_report} "
        f"({report['validation_status']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
