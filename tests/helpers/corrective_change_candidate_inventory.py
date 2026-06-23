"""CA5 corrective-change candidate inventory helpers (read-side only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

DEFAULT_DISCOVERY_KEYWORDS: tuple[str, ...] = (
    "fix",
    "bug",
    "repair",
    "restore",
    "prevent",
    "preserve",
    "guard",
    "regression",
    "fallback",
    "routing",
    "replay",
    "mutation",
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

QUALIFICATION_CHECKLIST: tuple[str, ...] = (
    "Concrete defect response is evidenced (wrong, failing, missing, leaked, shortened, misrouted, or unsafe behavior).",
    "At least one production/runtime source file under game/ or static/ changes.",
    "Primary intent is corrective; planned architecture, extraction, or feature delivery is excluded unless the defect boundary is separable.",
    "Commit boundary is reviewable (not a merge; repair fanout can be attributed honestly).",
    "Confidence is high or medium before promotion into a future cohort.",
)

EXCLUSION_CHECKLIST: tuple[str, ...] = (
    "Snapshot/data-only change with no production source repair or regression lock.",
    "Docs-only, test-only, tooling-only, or metric-only commit.",
    "Feature, governance, or architecture work without a separable defect repair.",
    "Merge commit or unreviewably mixed intent.",
    "Keyword nomination alone without matching defect and repair evidence.",
)


@dataclass(frozen=True)
class CandidateCommit:
    commit_hash: str
    date: str
    subject: str
    files_touched: int
    production_files_touched: int
    test_files_touched: int
    generated_files_touched: int
    matched_keywords: tuple[str, ...]


@dataclass(frozen=True)
class ReviewQueueRow:
    commit_hash: str
    reviewed: bool
    qualifies: str
    confidence: str
    defect_statement: str
    repair_family: str
    notes: str


def normalize_keywords(keywords: Sequence[str] | None) -> tuple[str, ...]:
    if keywords is None:
        return DEFAULT_DISCOVERY_KEYWORDS
    normalized = tuple(sorted({str(keyword).strip().lower() for keyword in keywords if str(keyword).strip()}))
    if not normalized:
        raise ValueError("keyword list must not be empty")
    return normalized


def matched_keywords_for_subject(subject: str, keywords: Sequence[str]) -> tuple[str, ...]:
    lowered = str(subject or "").lower()
    return tuple(keyword for keyword in keywords if keyword in lowered)


def subject_matches_keywords(subject: str, keywords: Sequence[str]) -> bool:
    return bool(matched_keywords_for_subject(subject, keywords))


def sort_candidates(candidates: Sequence[CandidateCommit]) -> list[CandidateCommit]:
    """Sort candidates by date descending, then commit hash ascending."""
    return sorted(
        candidates,
        key=lambda candidate: (-int(candidate.date.replace("-", "")), candidate.commit_hash),
    )


def deduplicate_candidates(candidates: Sequence[CandidateCommit]) -> list[CandidateCommit]:
    """Return one candidate per commit hash, keeping the first occurrence."""
    seen: set[str] = set()
    unique: list[CandidateCommit] = []
    for candidate in candidates:
        if candidate.commit_hash in seen:
            continue
        seen.add(candidate.commit_hash)
        unique.append(candidate)
    return unique


def validate_unique_commit_hashes(candidates: Sequence[CandidateCommit]) -> list[str]:
    seen: dict[str, int] = {}
    for candidate in candidates:
        seen[candidate.commit_hash] = seen.get(candidate.commit_hash, 0) + 1
    duplicates = sorted(commit_hash for commit_hash, count in seen.items() if count > 1)
    if not duplicates:
        return []
    return [f"duplicate commit_hash value(s): {', '.join(duplicates)}"]
