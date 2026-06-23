"""CA6 post-baseline corrective cohort loader and validation."""
from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

DEFAULT_COHORT_CSV_PATH = "docs/audits/CA_post_baseline_cohort.csv"
DEFAULT_EXCLUSIONS_CSV_PATH = "docs/audits/CA_post_baseline_exclusions.csv"
DEFAULT_REVIEW_QUEUE_PATH = "docs/audits/ca_review_queue.csv"
DEFAULT_CA6_REPORT_PATH = "artifacts/ca6_reviewed_cohort_report.md"

POST_BASELINE_COHORT_FIELDS: tuple[str, ...] = (
    "cohort_id",
    "commit_hash",
    "date",
    "title",
    "confidence",
    "defect_statement",
    "repair_family",
    "review_notes",
)

POST_BASELINE_EXCLUSION_FIELDS: tuple[str, ...] = (
    "commit_hash",
    "date",
    "title",
    "exclusion_reason",
    "review_notes",
)

REVIEW_QUEUE_FIELDS: tuple[str, ...] = (
    "commit_hash",
    "reviewed",
    "qualifies",
    "confidence",
    "defect_statement",
    "repair_family",
    "notes",
)


@dataclass(frozen=True)
class PostBaselineCohortRow:
    cohort_id: str
    commit_hash: str
    date: str
    title: str
    confidence: str
    defect_statement: str
    repair_family: str
    review_notes: str


@dataclass(frozen=True)
class PostBaselineExclusionRow:
    commit_hash: str
    date: str
    title: str
    exclusion_reason: str
    review_notes: str


@dataclass(frozen=True)
class ReviewQueueRow:
    commit_hash: str
    reviewed: bool
    qualifies: bool | None
    confidence: str
    defect_statement: str
    repair_family: str
    notes: str


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root if repo_root is not None else Path(__file__).resolve().parents[2]


def _parse_bool(value: str) -> bool:
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def _parse_optional_bool(value: str) -> bool | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def load_post_baseline_cohort(csv_path: str | Path | None = None) -> list[PostBaselineCohortRow]:
    target = Path(csv_path or DEFAULT_COHORT_CSV_PATH)
    if not target.is_absolute():
        target = _repo_root(None) / target
    rows: list[PostBaselineCohortRow] = []
    if not target.is_file():
        return rows
    with target.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            commit_hash = str(raw.get("commit_hash") or "").strip()
            if not commit_hash:
                continue
            rows.append(
                PostBaselineCohortRow(
                    cohort_id=str(raw.get("cohort_id") or "").strip(),
                    commit_hash=commit_hash,
                    date=str(raw.get("date") or "").strip(),
                    title=str(raw.get("title") or "").strip(),
                    confidence=str(raw.get("confidence") or "").strip(),
                    defect_statement=str(raw.get("defect_statement") or "").strip(),
                    repair_family=str(raw.get("repair_family") or "").strip(),
                    review_notes=str(raw.get("review_notes") or "").strip(),
                )
            )
    return rows


def load_post_baseline_exclusions(
    csv_path: str | Path | None = None,
) -> list[PostBaselineExclusionRow]:
    target = Path(csv_path or DEFAULT_EXCLUSIONS_CSV_PATH)
    if not target.is_absolute():
        target = _repo_root(None) / target
    rows: list[PostBaselineExclusionRow] = []
    with target.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            commit_hash = str(raw.get("commit_hash") or "").strip()
            if not commit_hash:
                continue
            rows.append(
                PostBaselineExclusionRow(
                    commit_hash=commit_hash,
                    date=str(raw.get("date") or "").strip(),
                    title=str(raw.get("title") or "").strip(),
                    exclusion_reason=str(raw.get("exclusion_reason") or "").strip(),
                    review_notes=str(raw.get("review_notes") or "").strip(),
                )
            )
    return rows


def load_review_queue(csv_path: str | Path | None = None) -> list[ReviewQueueRow]:
    target = Path(csv_path or DEFAULT_REVIEW_QUEUE_PATH)
    if not target.is_absolute():
        target = _repo_root(None) / target
    rows: list[ReviewQueueRow] = []
    with target.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            commit_hash = str(raw.get("commit_hash") or "").strip()
            if not commit_hash:
                continue
            rows.append(
                ReviewQueueRow(
                    commit_hash=commit_hash,
                    reviewed=_parse_bool(str(raw.get("reviewed") or "")),
                    qualifies=_parse_optional_bool(str(raw.get("qualifies") or "")),
                    confidence=str(raw.get("confidence") or "").strip(),
                    defect_statement=str(raw.get("defect_statement") or "").strip(),
                    repair_family=str(raw.get("repair_family") or "").strip(),
                    notes=str(raw.get("notes") or "").strip(),
                )
            )
    return rows


def validate_required_columns(fieldnames: Sequence[str] | None, required: Sequence[str]) -> list[str]:
    if not fieldnames:
        return ["CSV has no header row"]
    present = {name.strip() for name in fieldnames if name}
    missing = [column for column in required if column not in present]
    if missing:
        return [f"missing required column(s): {', '.join(missing)}"]
    return []


def validate_unique_commit_hashes(commit_hashes: Sequence[str]) -> list[str]:
    seen: dict[str, int] = {}
    for commit_hash in commit_hashes:
        seen[commit_hash] = seen.get(commit_hash, 0) + 1
    duplicates = sorted(commit_hash for commit_hash, count in seen.items() if count > 1)
    if not duplicates:
        return []
    return [f"duplicate commit_hash value(s): {', '.join(duplicates)}"]


def validate_post_baseline_cohort_schema(rows: Sequence[PostBaselineCohortRow]) -> list[str]:
    errors: list[str] = []
    cohort_ids: list[str] = []
    commit_hashes: list[str] = []
    for row in rows:
        cohort_ids.append(row.cohort_id)
        commit_hashes.append(row.commit_hash)
        if not row.cohort_id:
            errors.append(f"{row.commit_hash}: missing cohort_id")
        if not row.date:
            errors.append(f"{row.cohort_id or row.commit_hash}: missing date")
        if not row.title:
            errors.append(f"{row.cohort_id or row.commit_hash}: missing title")
        if not row.confidence:
            errors.append(f"{row.cohort_id}: qualifying row missing confidence")
        if row.confidence not in {"high", "medium"}:
            errors.append(f"{row.cohort_id}: confidence must be high or medium")
        if not row.defect_statement:
            errors.append(f"{row.cohort_id}: qualifying row missing defect_statement")
        if not row.repair_family:
            errors.append(f"{row.cohort_id}: qualifying row missing repair_family")
    errors.extend(validate_unique_commit_hashes(commit_hashes))
    if cohort_ids:
        seen_ids: dict[str, int] = {}
        for cohort_id in cohort_ids:
            seen_ids[cohort_id] = seen_ids.get(cohort_id, 0) + 1
        duplicates = sorted(item for item, count in seen_ids.items() if count > 1)
        if duplicates:
            errors.append(f"duplicate cohort_id value(s): {', '.join(duplicates)}")
    return errors


def validate_post_baseline_exclusions_schema(rows: Sequence[PostBaselineExclusionRow]) -> list[str]:
    errors: list[str] = []
    commit_hashes: list[str] = []
    for row in rows:
        commit_hashes.append(row.commit_hash)
        if not row.date:
            errors.append(f"{row.commit_hash}: missing date")
        if not row.title:
            errors.append(f"{row.commit_hash}: missing title")
        if not row.exclusion_reason:
            errors.append(f"{row.commit_hash}: exclusion row missing exclusion_reason")
    errors.extend(validate_unique_commit_hashes(commit_hashes))
    return errors


def validate_review_queue_complete(rows: Sequence[ReviewQueueRow]) -> list[str]:
    errors: list[str] = []
    for row in rows:
        if not row.reviewed:
            errors.append(f"{row.commit_hash}: reviewed=false remains in queue")
        if row.qualifies is None:
            errors.append(f"{row.commit_hash}: qualifies decision missing after review")
    return errors


def validate_post_baseline_partition(
    cohort_rows: Sequence[PostBaselineCohortRow],
    exclusion_rows: Sequence[PostBaselineExclusionRow],
    review_queue_rows: Sequence[ReviewQueueRow],
) -> list[str]:
    errors: list[str] = []
    cohort_hashes = {row.commit_hash for row in cohort_rows}
    exclusion_hashes = {row.commit_hash for row in exclusion_rows}
    overlap = cohort_hashes & exclusion_hashes
    if overlap:
        errors.append(f"commit hash(es) appear in both cohort and exclusions: {', '.join(sorted(overlap))}")

    reviewed_hashes = {row.commit_hash for row in review_queue_rows if row.reviewed}
    qualifying_hashes = {row.commit_hash for row in review_queue_rows if row.qualifies is True}
    excluded_hashes = {row.commit_hash for row in review_queue_rows if row.qualifies is False}

    if cohort_hashes != qualifying_hashes:
        errors.append("cohort CSV does not match reviewed qualifies=true queue rows")
    if exclusion_hashes != excluded_hashes:
        errors.append("exclusions CSV does not match reviewed qualifies=false queue rows")
    if reviewed_hashes != cohort_hashes | exclusion_hashes:
        errors.append("review queue reviewed set does not partition into cohort and exclusions")
    return errors


def build_cohort_summary(
    cohort_rows: Sequence[PostBaselineCohortRow],
    exclusion_rows: Sequence[PostBaselineExclusionRow],
    review_queue_rows: Sequence[ReviewQueueRow],
) -> dict[str, Any]:
    reviewed_count = sum(1 for row in review_queue_rows if row.reviewed)
    confidence = Counter(row.confidence for row in cohort_rows if row.confidence)
    families = Counter(row.repair_family for row in cohort_rows if row.repair_family)
    return {
        "candidates_reviewed": reviewed_count,
        "qualifying_fixes": len(cohort_rows),
        "exclusions": len(exclusion_rows),
        "confidence_distribution": dict(sorted(confidence.items())),
        "repair_family_distribution": dict(sorted(families.items())),
    }


def validate_post_baseline_cohort(
    *,
    cohort_csv_path: str | Path | None = None,
    exclusions_csv_path: str | Path | None = None,
    review_queue_path: str | Path | None = None,
) -> list[str]:
    root = _repo_root(None)
    cohort_path = Path(cohort_csv_path or DEFAULT_COHORT_CSV_PATH)
    exclusions_path = Path(exclusions_csv_path or DEFAULT_EXCLUSIONS_CSV_PATH)
    queue_path = Path(review_queue_path or DEFAULT_REVIEW_QUEUE_PATH)
    if not cohort_path.is_absolute():
        cohort_path = root / cohort_path
    if not exclusions_path.is_absolute():
        exclusions_path = root / exclusions_path
    if not queue_path.is_absolute():
        queue_path = root / queue_path

    errors: list[str] = []
    if cohort_path.is_file():
        with cohort_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            errors.extend(validate_required_columns(reader.fieldnames, POST_BASELINE_COHORT_FIELDS))
    else:
        errors.append(f"missing cohort CSV: {cohort_path}")

    with exclusions_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        errors.extend(validate_required_columns(reader.fieldnames, POST_BASELINE_EXCLUSION_FIELDS))

    with queue_path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        errors.extend(validate_required_columns(reader.fieldnames, REVIEW_QUEUE_FIELDS))

    if errors:
        return errors

    cohort_rows = load_post_baseline_cohort(cohort_path)
    exclusion_rows = load_post_baseline_exclusions(exclusions_path)
    queue_rows = load_review_queue(queue_path)

    errors.extend(validate_post_baseline_cohort_schema(cohort_rows))
    errors.extend(validate_post_baseline_exclusions_schema(exclusion_rows))
    errors.extend(validate_review_queue_complete(queue_rows))
    errors.extend(validate_post_baseline_partition(cohort_rows, exclusion_rows, queue_rows))
    return errors


def render_ca6_reviewed_cohort_report_md(summary: Mapping[str, Any]) -> str:
    cohort_rows = summary.get("qualifying_rows") or []
    exclusion_rows = summary.get("exclusion_rows") or []
    stats = summary.get("stats") or {}
    readiness = summary.get("readiness") or {}

    lines = [
        "# CA6 Reviewed Post-Baseline Corrective Cohort Report",
        "",
        "> CA6 human review of CA5 intake candidates against CA1 qualification standards.",
        "",
        "## 1. Review Summary",
        "",
        f"- **Candidates reviewed:** {stats.get('candidates_reviewed', 0)}",
        f"- **Qualifying fixes:** {stats.get('qualifying_fixes', 0)}",
        f"- **Exclusions:** {stats.get('exclusions', 0)}",
        "",
        "## 2. Qualifying Fixes",
        "",
    ]
    if cohort_rows:
        lines.extend(
            [
                "| Cohort ID | Commit | Date | Title | Confidence | Repair family |",
                "|---|---|---|---|---|---|",
            ]
        )
        for row in cohort_rows:
            title = str(row.get("title") or "").replace("|", "\\|")
            lines.append(
                f"| {row.get('cohort_id')} | `{str(row.get('commit_hash') or '')[:7]}` | "
                f"{row.get('date')} | {title} | {row.get('confidence')} | {row.get('repair_family')} |"
            )
    else:
        lines.append("_No qualifying post-baseline corrective fixes were identified in this review window._")
    lines.extend(["", "## 3. Exclusions", ""])
    if exclusion_rows:
        lines.extend(["| Commit | Date | Title | Exclusion reason |", "|---|---|---|---|"])
        for row in exclusion_rows:
            title = str(row.get("title") or "").replace("|", "\\|")
            reason = str(row.get("exclusion_reason") or "").replace("|", "\\|")
            lines.append(
                f"| `{str(row.get('commit_hash') or '')[:7]}` | {row.get('date')} | {title} | {reason} |"
            )
    lines.extend(["", "## 4. Confidence Distribution", ""])
    confidence = stats.get("confidence_distribution") or {}
    if confidence:
        for key, count in confidence.items():
            lines.append(f"- **{key}:** {count}")
    else:
        lines.append("_No qualifying fixes; confidence distribution is empty._")
    lines.extend(["", "## 5. Repair Family Distribution", ""])
    families = stats.get("repair_family_distribution") or {}
    if families:
        for key, count in families.items():
            lines.append(f"- **{key}:** {count}")
    else:
        lines.append("_No qualifying fixes; repair family distribution is empty._")
    lines.extend(
        [
            "",
            "## 6. Cohort Readiness Assessment",
            "",
            f"- **Review complete:** {readiness.get('review_complete', False)}",
            f"- **Schema valid:** {readiness.get('schema_valid', False)}",
            f"- **Ready for CA3 measurement:** {readiness.get('ready_for_measurement', False)}",
            f"- **Assessment:** {readiness.get('assessment', '')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_ca6_reviewed_cohort_report(
    output_path: str | Path | None = None,
    *,
    cohort_csv_path: str | Path | None = None,
    exclusions_csv_path: str | Path | None = None,
    review_queue_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> tuple[dict[str, Any], str]:
    errors = validate_post_baseline_cohort(
        cohort_csv_path=cohort_csv_path,
        exclusions_csv_path=exclusions_csv_path,
        review_queue_path=review_queue_path,
    )
    if errors:
        raise ValueError("CA6 cohort validation failed:\n" + "\n".join(f"- {err}" for err in errors))

    cohort_rows = load_post_baseline_cohort(cohort_csv_path)
    exclusion_rows = load_post_baseline_exclusions(exclusions_csv_path)
    queue_rows = load_review_queue(review_queue_path)
    stats = build_cohort_summary(cohort_rows, exclusion_rows, queue_rows)

    qualifying_count = len(cohort_rows)
    readiness = {
        "review_complete": all(row.reviewed for row in queue_rows),
        "schema_valid": True,
        "ready_for_measurement": qualifying_count > 0,
        "assessment": (
            "Post-baseline cohort review is complete and validated. "
            f"{qualifying_count} qualifying fix(es) are ready for CA3 measurement."
            if qualifying_count
            else "Post-baseline cohort review is complete and validated. "
            "No qualifying corrective fixes were found after CA4; the cohort CSV remains an empty authority shell until future reviews add qualifying rows."
        ),
    }

    payload = {
        "stats": stats,
        "readiness": readiness,
        "qualifying_rows": [row.__dict__ for row in cohort_rows],
        "exclusion_rows": [row.__dict__ for row in exclusion_rows],
    }
    markdown = render_ca6_reviewed_cohort_report_md(payload)
    target = Path(output_path or DEFAULT_CA6_REPORT_PATH)
    if not target.is_absolute():
        target = _repo_root(repo_root) / target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return payload, markdown
