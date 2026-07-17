"""Recurrence governance documentation contract locks (CO99, CO100).

Documentation-only assertions — no runtime recurrence behavior checks.
"""
from __future__ import annotations

from pathlib import Path

from tests.helpers.replay_bug_recurrence_serialization import (
    RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH,
    RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_IMMATURE,
)
from tests.helpers.replay_bug_recurrence_statistics import RECURRENCE_GRADUATION_AUDIT_DOC_PATH


def test_co99_recurrence_registry_documents_operational_graduation_authority():
    root = Path(__file__).resolve().parents[1]
    registry = (root / "docs" / "audits" / "CG_recurrence_taxonomy_registry.md").read_text(encoding="utf-8")
    bq16 = (root / RECURRENCE_GRADUATION_AUDIT_DOC_PATH).read_text(encoding="utf-8")
    bqc4 = (root / RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH).read_text(encoding="utf-8")

    assert "Operational graduation authority" in registry or "operational graduation authority" in registry.lower()
    assert "BQ16_recurrence_graduation_audit.md" in registry
    assert "BQC4_final_graduation_decision.md" in registry
    assert "CO96_attribution_program_closeout.md" in registry
    assert "only active graduation track" in registry.lower() or "Only remaining active graduation track" in registry
    assert "not graduated" in registry.lower()

    assert "Governance context (CO99)" in bq16
    assert "Operational graduation baseline (CO99)" in bq16
    assert "Program graduated: `false`" in bq16

    assert RECURRENCE_FINAL_GRADUATION_RECOMMENDATION_IMMATURE in bqc4 or (
        "operationally immature" in bqc4.lower()
    )


def test_co99_recurrence_doc_paths_match_governance_constants():
    assert RECURRENCE_GRADUATION_AUDIT_DOC_PATH.as_posix() == "docs/audits/BQ16_recurrence_graduation_audit.md"
    assert RECURRENCE_FINAL_GRADUATION_DECISION_DOC_PATH.as_posix() == "docs/audits/BQC4_final_graduation_decision.md"


def test_co100_protected_replay_observation_runbook_references_operational_graduation_authority():
    root = Path(__file__).resolve().parents[1]
    runbook_path = root / "docs" / "runbooks" / "protected_replay_observation_collection.md"
    assert runbook_path.is_file(), "protected replay observation runbook must exist"
    runbook = runbook_path.read_text(encoding="utf-8")

    assert "BQ16_recurrence_graduation_audit.md" in runbook
    assert "BQC4_final_graduation_decision.md" in runbook
    assert "BQ36_recurrence_write_path_audit.md" in runbook
    assert "CG_recurrence_taxonomy_registry.md" in runbook
    assert "Operational graduation baseline (CO99)" in runbook or "CO99 operational graduation baseline" in runbook
    assert "Graduation authority" in runbook or "graduation authority" in runbook.lower()
    assert "Taxonomy authority" in runbook or "taxonomy authority" in runbook.lower()
