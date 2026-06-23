"""CA1 reviewed corrective-change locality cohort authority (read-side only).

Loads and validates the human-reviewed cohort CSV under docs/audits/.
Does not mine git history, integrate recurrence, or modify runtime behavior.
"""
from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

DEFAULT_COHORT_CSV_PATH = "docs/audits/CA_corrective_change_locality_cohort.csv"
DEFAULT_REPORT_PATH = "artifacts/ca1_cohort_authority_report.md"

REQUIRED_COLUMNS: tuple[str, ...] = (
    "cohort_id",
    "commit_hash",
    "date",
    "title",
    "qualifies",
    "confidence",
    "defect_statement",
    "repair_family",
    "recurrence_evidence_status",
    "total_files_touched",
    "production_files_touched",
    "test_files_touched",
    "docs_files_touched",
    "tooling_files_touched",
    "fixture_files_touched",
    "generated_files_touched",
    "effective_files_touched",
    "exclusion_reason",
)

COUNT_COLUMNS: tuple[str, ...] = (
    "total_files_touched",
    "production_files_touched",
    "test_files_touched",
    "docs_files_touched",
    "tooling_files_touched",
    "fixture_files_touched",
    "generated_files_touched",
    "effective_files_touched",
)

QUALIFYING_TEXT_COLUMNS: tuple[str, ...] = (
    "confidence",
    "defect_statement",
    "repair_family",
    "recurrence_evidence_status",
)


@dataclass(frozen=True)
class CorrectiveChangeLocalityCohortRow:
    cohort_id: str
    commit_hash: str
    date: str
    title: str
    qualifies: bool
    confidence: str
    defect_statement: str
    repair_family: str
    recurrence_evidence_status: str
    total_files_touched: int
    production_files_touched: int
    test_files_touched: int
    docs_files_touched: int
    tooling_files_touched: int
    fixture_files_touched: int
    generated_files_touched: int
    effective_files_touched: int
    exclusion_reason: str

    @property
    def is_exclusion(self) -> bool:
        return not self.qualifies


def _parse_bool(value: str) -> bool:
    normalized = str(value or "").strip().lower()
    if normalized in {"true", "1", "yes"}:
        return True
    if normalized in {"false", "0", "no"}:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def _parse_int(value: str, *, field: str, cohort_id: str) -> int:
    text = str(value if value is not None else "").strip()
    if not text:
        raise ValueError(f"{cohort_id}: missing required count {field}")
    try:
        return int(text)
    except ValueError as exc:
        raise ValueError(f"{cohort_id}: invalid integer for {field}: {value!r}") from exc


def _row_from_raw(raw: dict[str, str]) -> CorrectiveChangeLocalityCohortRow:
    cohort_id = str(raw.get("cohort_id") or "").strip()
    if not cohort_id:
        raise ValueError("cohort row missing cohort_id")

    qualifies = _parse_bool(str(raw.get("qualifies") or ""))
    counts = {
        field: _parse_int(str(raw.get(field) or ""), field=field, cohort_id=cohort_id)
        for field in COUNT_COLUMNS
    }

    return CorrectiveChangeLocalityCohortRow(
        cohort_id=cohort_id,
        commit_hash=str(raw.get("commit_hash") or "").strip(),
        date=str(raw.get("date") or "").strip(),
        title=str(raw.get("title") or "").strip(),
        qualifies=qualifies,
        confidence=str(raw.get("confidence") or "").strip(),
        defect_statement=str(raw.get("defect_statement") or "").strip(),
        repair_family=str(raw.get("repair_family") or "").strip(),
        recurrence_evidence_status=str(raw.get("recurrence_evidence_status") or "").strip(),
        exclusion_reason=str(raw.get("exclusion_reason") or "").strip(),
        **counts,
    )


def load_cohort(csv_path: str | Path | None = None) -> list[CorrectiveChangeLocalityCohortRow]:
    """Load reviewed corrective-change locality cohort rows from CSV."""
    target = Path(csv_path or DEFAULT_COHORT_CSV_PATH)
    rows: list[CorrectiveChangeLocalityCohortRow] = []
    with target.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{target}: CSV has no header row")
        for raw in reader:
            if not any(str(value or "").strip() for value in raw.values()):
                continue
            rows.append(_row_from_raw(raw))
    return rows


def validate_required_columns(fieldnames: Sequence[str] | None) -> list[str]:
    """Return errors for missing required CSV columns."""
    if not fieldnames:
        return ["CSV has no header row"]
    present = {name.strip() for name in fieldnames if name}
    missing = [column for column in REQUIRED_COLUMNS if column not in present]
    if missing:
        return [f"missing required column(s): {', '.join(missing)}"]
    return []


def validate_schema(rows: Sequence[CorrectiveChangeLocalityCohortRow]) -> list[str]:
    """Return schema validation errors for loaded cohort rows."""
    errors: list[str] = []
    if not rows:
        errors.append("cohort is empty")
        return errors

    for row in rows:
        if not row.cohort_id:
            errors.append("row missing cohort_id")
        if not row.commit_hash:
            errors.append(f"{row.cohort_id or '<unknown>'}: missing commit_hash")
        if not row.date:
            errors.append(f"{row.cohort_id}: missing date")
        if not row.title:
            errors.append(f"{row.cohort_id}: missing title")

        if row.qualifies:
            for field in QUALIFYING_TEXT_COLUMNS:
                if not getattr(row, field):
                    errors.append(f"{row.cohort_id}: qualifying row missing {field}")
            if row.exclusion_reason:
                errors.append(f"{row.cohort_id}: qualifying row must not set exclusion_reason")
        else:
            if not row.exclusion_reason:
                errors.append(f"{row.cohort_id}: exclusion row missing exclusion_reason")

        expected_effective = row.total_files_touched - row.generated_files_touched
        if row.effective_files_touched != expected_effective:
            errors.append(
                f"{row.cohort_id}: effective_files_touched ({row.effective_files_touched}) "
                f"!= total_files_touched - generated_files_touched ({expected_effective})"
            )

        for field in COUNT_COLUMNS:
            value = getattr(row, field)
            if value < 0:
                errors.append(f"{row.cohort_id}: {field} must be non-negative")

    errors.extend(validate_cohort_id_uniqueness(rows))
    errors.extend(validate_commit_hash_uniqueness(rows))
    return errors


def validate_cohort_id_uniqueness(rows: Sequence[CorrectiveChangeLocalityCohortRow]) -> list[str]:
    """Return errors when cohort_id values are duplicated."""
    seen: dict[str, int] = {}
    for row in rows:
        seen[row.cohort_id] = seen.get(row.cohort_id, 0) + 1
    duplicates = sorted(cohort_id for cohort_id, count in seen.items() if count > 1)
    if not duplicates:
        return []
    return [f"duplicate cohort_id value(s): {', '.join(duplicates)}"]


def validate_commit_hash_uniqueness(rows: Sequence[CorrectiveChangeLocalityCohortRow]) -> list[str]:
    """Return errors when commit_hash values are duplicated."""
    seen: dict[str, int] = {}
    for row in rows:
        seen[row.commit_hash] = seen.get(row.commit_hash, 0) + 1
    duplicates = sorted(commit_hash for commit_hash, count in seen.items() if count > 1)
    if not duplicates:
        return []
    return [f"duplicate commit_hash value(s): {', '.join(duplicates)}"]


def validate_no_missing_counts(rows: Sequence[CorrectiveChangeLocalityCohortRow]) -> list[str]:
    """Return errors when any count column is missing or invalid."""
    errors: list[str] = []
    for row in rows:
        for field in COUNT_COLUMNS:
            value = getattr(row, field)
            if value is None:
                errors.append(f"{row.cohort_id}: missing count {field}")
    return errors


def validate_cohort(csv_path: str | Path | None = None) -> list[str]:
    """Load cohort CSV and return all validation errors; empty when valid."""
    target = Path(csv_path or DEFAULT_COHORT_CSV_PATH)
    with target.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        column_errors = validate_required_columns(reader.fieldnames)
        if column_errors:
            return column_errors

    rows = load_cohort(target)
    errors = validate_schema(rows)
    errors.extend(validate_no_missing_counts(rows))
    return errors


def qualifying_rows(rows: Sequence[CorrectiveChangeLocalityCohortRow]) -> list[CorrectiveChangeLocalityCohortRow]:
    return [row for row in rows if row.qualifies]


def exclusion_rows(rows: Sequence[CorrectiveChangeLocalityCohortRow]) -> list[CorrectiveChangeLocalityCohortRow]:
    return [row for row in rows if not row.qualifies]


def _distribution_lines(counter: Counter[str], *, title: str) -> list[str]:
    lines = [f"### {title}", ""]
    if not counter:
        lines.append("_No values._")
        lines.append("")
        return lines
    for key, count in sorted(counter.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- **{key}**: {count}")
    lines.append("")
    return lines


def build_ca1_cohort_authority_report(
    rows: Sequence[CorrectiveChangeLocalityCohortRow],
) -> dict[str, object]:
    """Build machine-readable CA1 cohort authority summary."""
    qualifying = qualifying_rows(rows)
    exclusions = exclusion_rows(rows)
    confidence = Counter(row.confidence for row in qualifying if row.confidence)
    repair_family = Counter(row.repair_family for row in qualifying if row.repair_family)
    recurrence = Counter(
        row.recurrence_evidence_status for row in qualifying if row.recurrence_evidence_status
    )
    return {
        "schema_version": 1,
        "qualifying_count": len(qualifying),
        "exclusion_count": len(exclusions),
        "confidence_distribution": dict(sorted(confidence.items())),
        "repair_family_distribution": dict(sorted(repair_family.items())),
        "recurrence_evidence_distribution": dict(sorted(recurrence.items())),
    }


def render_ca1_cohort_authority_report_md(
    rows: Sequence[CorrectiveChangeLocalityCohortRow],
) -> str:
    """Render human-readable CA1 cohort authority report markdown."""
    summary = build_ca1_cohort_authority_report(rows)
    qualifying = qualifying_rows(rows)
    exclusions = exclusion_rows(rows)
    confidence = Counter(row.confidence for row in qualifying if row.confidence)
    repair_family = Counter(row.repair_family for row in qualifying if row.repair_family)
    recurrence = Counter(
        row.recurrence_evidence_status for row in qualifying if row.recurrence_evidence_status
    )

    lines = [
        "# CA1 Corrective Change Locality Cohort Authority Report",
        "",
        "> CA1 repository-owned reviewed cohort authority. Read-side validation and reporting only.",
        "",
        "## Summary",
        "",
        f"- **Qualifying entries:** {summary['qualifying_count']}",
        f"- **Exclusion entries:** {summary['exclusion_count']}",
        f"- **Total rows:** {len(rows)}",
        "",
    ]
    lines.extend(_distribution_lines(confidence, title="Confidence distribution (qualifying)"))
    lines.extend(_distribution_lines(repair_family, title="Repair family distribution (qualifying)"))
    lines.extend(
        _distribution_lines(recurrence, title="Recurrence evidence distribution (qualifying)")
    )

    lines.extend(["## Qualifying cohort", ""])
    for row in qualifying:
        lines.append(
            f"- **{row.cohort_id}** `{row.commit_hash[:7]}` ({row.date}) — "
            f"{row.repair_family}, confidence={row.confidence}, "
            f"total={row.total_files_touched}, effective={row.effective_files_touched}"
        )
    lines.append("")

    lines.extend(["## Exclusion controls", ""])
    for row in exclusions:
        lines.append(
            f"- **{row.cohort_id}** `{row.commit_hash[:7]}` — {row.exclusion_reason}"
        )
    lines.append("")

    return "\n".join(lines)


def write_ca1_cohort_authority_report(
    output_path: str | Path | None = None,
    csv_path: str | Path | None = None,
) -> tuple[dict[str, object], str]:
    """Validate cohort authority and write the CA1 report markdown."""
    errors = validate_cohort(csv_path)
    if errors:
        raise ValueError("cohort validation failed:\n" + "\n".join(f"- {err}" for err in errors))
    rows = load_cohort(csv_path)
    summary = build_ca1_cohort_authority_report(rows)
    markdown = render_ca1_cohort_authority_report_md(rows)
    target = Path(output_path or DEFAULT_REPORT_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(markdown, encoding="utf-8")
    return summary, markdown
