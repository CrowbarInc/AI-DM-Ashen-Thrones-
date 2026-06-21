"""Fast BU20/BU21 split-owner acceptance matrix contract gate.

Locks matrix row counts, dashboard case-id parity, checked-in audit report text,
and lightweight classifier/dashboard builder surfaces without running the full
failure dashboard probe suite.

Included in the default fast lane (`pytest -m "not transcript and not slow"`) and
CI convergence-checks via `scripts/check_split_owner_acceptance_matrix.py`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers.convergence_ci_inventory_contract import (
    assert_convergence_ci_inventory_split_owner_doc_contract,
    convergence_inventory_doc_contract_errors,
)
from tests.helpers.failure_classification_sync import (
    SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS,
    SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_FEM_PROJECTION_ROWS,
    SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_LEGACY_ONLY_ROWS,
    SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_TOTAL_ROWS,
    SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES,
    assert_split_owner_acceptance_matrix_contract,
    render_split_owner_acceptance_matrix_report,
    split_owner_acceptance_matrix_contract_misalignments,
    split_owner_acceptance_matrix_counts,
)

pytestmark = pytest.mark.split_owner_matrix_contract

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_split_owner_acceptance_matrix_contract_is_locked() -> None:
    """BU20: one fast gate for matrix/report/dashboard/FEM/classifier builder drift."""
    assert SPLIT_OWNER_DASHBOARD_CASE_ID_ALIASES == {}
    assert_split_owner_acceptance_matrix_contract(repo_root=REPO_ROOT)


def test_split_owner_acceptance_matrix_contract_counts_are_explicit() -> None:
    counts = split_owner_acceptance_matrix_counts()
    assert counts["total_rows"] == SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_TOTAL_ROWS
    assert counts["dashboard_covered_rows"] == SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS
    assert counts["fem_projection_rows"] == SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_FEM_PROJECTION_ROWS
    assert counts["legacy_only_rows"] == SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_LEGACY_ONLY_ROWS
    assert counts["dashboard_probes"] == SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS


def test_split_owner_acceptance_matrix_report_regeneration_mismatch_is_detected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report_dir = tmp_path / "docs" / "audits"
    report_dir.mkdir(parents=True)
    stale_report = report_dir / "BU15_split_owner_acceptance_matrix.md"
    stale_report.write_text("# stale report\n", encoding="utf-8")

    monkeypatch.setattr(
        "tests.helpers.failure_classification_sync.SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH",
        "docs/audits/BU15_split_owner_acceptance_matrix.md",
    )
    monkeypatch.setattr(
        "tests.helpers.failure_classification_sync.split_owner_acceptance_matrix_report_text",
        lambda *, repo_root=None: stale_report.read_text(encoding="utf-8"),
    )

    misalignments = split_owner_acceptance_matrix_contract_misalignments(repo_root=tmp_path)
    assert misalignments
    assert any("out of date" in item for item in misalignments)
    assert render_split_owner_acceptance_matrix_report() not in stale_report.read_text(encoding="utf-8")


def test_check_split_owner_acceptance_matrix_script_exits_zero() -> None:
    from scripts.check_split_owner_acceptance_matrix import main

    assert main(["--repo-root", str(REPO_ROOT)]) == 0


def test_refresh_split_owner_acceptance_matrix_script_default_exits_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """BU25: default refresh path on real repo with pytest subprocess mocked."""
    from scripts.refresh_split_owner_acceptance_matrix import main as refresh_main

    monkeypatch.setattr(
        "scripts.refresh_split_owner_acceptance_matrix._ops.run_split_owner_acceptance_matrix_pytest",
        lambda *, repo_root: 0,
    )
    assert refresh_main(["--repo-root", str(REPO_ROOT)]) == 0


def test_convergence_ci_inventory_split_owner_doc_contract_is_locked() -> None:
    """BU27/BU29: inventory, workflow, and BU28 navigation pointers stay aligned."""
    assert_convergence_ci_inventory_split_owner_doc_contract(repo_root=REPO_ROOT)


def test_convergence_ci_inventory_doc_contract_errors_are_actionable(
    tmp_path: Path,
) -> None:
    inventory_path = tmp_path / "docs" / "convergence_ci_inventory.md"
    inventory_path.parent.mkdir(parents=True)
    inventory_path.write_text("# Convergence CI inventory\n\n(stale stub)\n", encoding="utf-8")

    errors = convergence_inventory_doc_contract_errors(repo_root=tmp_path)

    assert errors
    assert any("governance discovery index header" in item for item in errors)
    assert any("check_split_owner_acceptance_matrix.py" in item for item in errors)
    assert any("Split-owner acceptance matrix governance" in item for item in errors)


def test_convergence_ci_inventory_missing_discovery_index_header_is_actionable(
    tmp_path: Path,
) -> None:
    _write_minimal_inventory_stub(tmp_path, include_discovery_index=False)
    _write_minimal_workflow_stub(tmp_path)
    _write_forward_pointer_stubs(tmp_path)

    errors = convergence_inventory_doc_contract_errors(repo_root=tmp_path)

    assert any("governance discovery index header" in item for item in errors)
    assert not any("audit README forward pointer" in item for item in errors)


def test_audits_readme_missing_inventory_forward_pointer_is_actionable(
    tmp_path: Path,
) -> None:
    _write_minimal_inventory_stub(tmp_path, include_discovery_index=True)
    _write_minimal_workflow_stub(tmp_path)
    _write_forward_pointer_stubs(tmp_path, include_audits_pointer=False)

    errors = convergence_inventory_doc_contract_errors(repo_root=tmp_path)

    assert any("docs/audits/README.md missing audit README forward pointer" in item for item in errors)


def test_tests_readme_missing_inventory_forward_pointer_is_actionable(
    tmp_path: Path,
) -> None:
    _write_minimal_inventory_stub(tmp_path, include_discovery_index=True)
    _write_minimal_workflow_stub(tmp_path)
    _write_forward_pointer_stubs(tmp_path, include_tests_readme_pointer=False)

    errors = convergence_inventory_doc_contract_errors(repo_root=tmp_path)

    assert any("tests/README_TESTS.md missing test README forward pointer" in item for item in errors)


def _write_minimal_inventory_stub(tmp_path: Path, *, include_discovery_index: bool) -> None:
    header = "# Convergence CI inventory\n\n"
    if include_discovery_index:
        header += "Governance discovery index\n\n"
    body = "\n".join(
        [
            "check_split_owner_acceptance_matrix.py",
            "refresh_split_owner_acceptance_matrix.py",
            "convergence-checks.yml",
            "Split-owner acceptance matrix governance",
            "docs/audits/README.md",
            "docs/audits/BU15_split_owner_acceptance_matrix.md",
            "make split-owner-matrix-check",
            "make split-owner-matrix-refresh",
        ]
    )
    path = tmp_path / "docs" / "convergence_ci_inventory.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + body, encoding="utf-8")


def _write_minimal_workflow_stub(tmp_path: Path) -> None:
    path = tmp_path / ".github" / "workflows" / "convergence-checks.yml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "name: convergence-checks\n"
        "run: python scripts/check_split_owner_acceptance_matrix.py\n"
        "Split-owner acceptance matrix contract\n",
        encoding="utf-8",
    )


def _write_forward_pointer_stubs(
    tmp_path: Path,
    *,
    include_audits_pointer: bool = True,
    include_tests_readme_pointer: bool = True,
) -> None:
    audits_path = tmp_path / "docs" / "audits" / "README.md"
    audits_path.parent.mkdir(parents=True, exist_ok=True)
    audits_text = "# Audit artifacts\n"
    if include_audits_pointer:
        audits_text += "convergence_ci_inventory.md\n"
    audits_path.write_text(audits_text, encoding="utf-8")

    tests_readme_path = tmp_path / "tests" / "README_TESTS.md"
    tests_readme_path.parent.mkdir(parents=True, exist_ok=True)
    tests_text = "# Running tests\n"
    if include_tests_readme_pointer:
        tests_text += "convergence_ci_inventory.md\n"
    tests_readme_path.write_text(tests_text, encoding="utf-8")
