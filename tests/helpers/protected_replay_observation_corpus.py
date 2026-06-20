"""Curated protected replay observation corpus for BQ data-volume expansion.

Maps controlled failure-classification shapes to existing protected golden replay
scenario identifiers. Report-only; does not change replay pass/fail behavior.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from tests.helpers.failure_dashboard_fixtures import classified_rows

PROTECTED_REPLAY_OBSERVATION_CORPUS_REPORT_PATH = (
    "artifacts/golden_replay/replay_failure_corpus_observations.md"
)
PROTECTED_REPLAY_OBSERVATION_EXPANSION_COMMAND = (
    "python tools/expand_protected_replay_observations.py"
)
PROTECTED_REPLAY_OBSERVATION_EXPANSION_GENERATED_AT = "2026-06-20T12:00:00Z"

# Existing protected golden replay scenarios from protected_replay_manifest.md.
_PROTECTED_SCENARIO_BINDINGS: tuple[tuple[str, str, str], ...] = (
    (
        "wrong_speaker",
        "wrong_speaker_strict_social_emission",
        "tests/test_golden_replay.py::test_golden_replay_wrong_speaker_strict_social_emission_structural_invariants",
    ),
    (
        "forced_fallback_source",
        "directed_npc_question",
        "tests/test_golden_replay.py::test_golden_replay_directed_npc_question_structural_invariants",
    ),
    (
        "sanitizer_leakage",
        "sanitizer_scaffold_leakage",
        "tests/test_golden_replay.py::test_golden_replay_sanitizer_scaffold_leakage_structural_invariants",
    ),
)

_FAILURE_TABLE_DRIFT_TYPES: dict[str, str] = {
    "selected_speaker_id": "structural_drift",
    "final_emitted_source": "structural_drift",
    "scaffold_leakage": "semantic_drift",
}

_FAILURE_TABLE_EXPECTED_ACTUAL: dict[str, tuple[str, str]] = {
    "selected_speaker_id": ("runner", "merchant"),
    "final_emitted_source": ("anti_reset_local_continuation_fallback", "global_scene_fallback"),
    "scaffold_leakage": ("false", "true"),
}


def _classified_row_by_probe_id() -> dict[str, dict[str, Any]]:
    return {str(row.get("scenario_id") or ""): dict(row) for row in classified_rows()}


def protected_replay_observation_expansion_rows() -> list[dict[str, Any]]:
    """Return commit-worthy protected observation rows mapped to protected scenarios."""
    by_probe = _classified_row_by_probe_id()
    rows: list[dict[str, Any]] = []
    for probe_id, protected_scenario_id, test_node_id in _PROTECTED_SCENARIO_BINDINGS:
        source = by_probe.get(probe_id)
        if not source:
            continue
        row = dict(source)
        row["scenario_id"] = protected_scenario_id
        row["test_node_id"] = test_node_id
        rows.append(row)
    return rows


def render_protected_replay_observation_corpus_report(
    *,
    command: str = PROTECTED_REPLAY_OBSERVATION_EXPANSION_COMMAND,
    generated_at: str = PROTECTED_REPLAY_OBSERVATION_EXPANSION_GENERATED_AT,
    rows: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    """Render the protected replay observation corpus as failure-report markdown."""
    expansion_rows = [dict(row) for row in (rows or protected_replay_observation_expansion_rows())]
    table_rows: list[str] = []
    for row in expansion_rows:
        field_path = str(row.get("field_path") or "")
        drift_type = _FAILURE_TABLE_DRIFT_TYPES.get(field_path, "structural_drift")
        expected, actual = _FAILURE_TABLE_EXPECTED_ACTUAL.get(field_path, ("expected", "actual"))
        table_rows.append(
            "| "
            + " | ".join(
                (
                    str(row.get("scenario_id") or ""),
                    str(row.get("test_node_id") or ""),
                    str(row.get("turn_index") or 0),
                    f"{field_path}: exact value mismatch",
                    drift_type,
                    expected,
                    actual,
                    str(row.get("category") or ""),
                    "medium",
                    str(row.get("primary_owner") or ""),
                    "none",
                    str(row.get("investigate_first") or ""),
                )
            )
            + " |"
        )

    return "\n".join(
        [
            "# Protected Replay Observation Corpus",
            "",
            "Report-only expansion corpus for protected replay recurrence history.",
            "Rows map controlled failure classifications to existing protected scenarios.",
            "",
            "## Run Summary",
            "",
            "- Status: `failed`",
            f"- Command: `{command}`",
            f"- Generated at: `{generated_at}`",
            f"- Artifact location: `{PROTECTED_REPLAY_OBSERVATION_CORPUS_REPORT_PATH}`",
            f"- Classified failures: `{len(expansion_rows)}`",
            "",
            "## Failure Table",
            "",
            "| Scenario | Test Node | Turn | Failed Invariant | Drift Type | Expected | Actual | Category | Severity | Primary Owner | Secondary Owner | Investigate First |",
            "|---|---|---:|---|---|---|---|---|---|---|---|---|",
            *table_rows,
            "",
        ]
    )
