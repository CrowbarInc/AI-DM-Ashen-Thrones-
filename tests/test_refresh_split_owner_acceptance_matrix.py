"""BU25 contract tests for split-owner matrix refresh/check CLI wrappers."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.helpers.failure_classification_sync import (
    SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS,
    SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_FEM_PROJECTION_ROWS,
    SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_LEGACY_ONLY_ROWS,
    SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_TOTAL_ROWS,
    render_split_owner_acceptance_matrix_report,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import split_owner_acceptance_matrix_ops as matrix_ops

pytestmark = pytest.mark.split_owner_matrix_contract

REPORT_REL = matrix_ops.SPLIT_OWNER_ACCEPTANCE_MATRIX_REPORT_REL_PATH
EXPECTED_COUNTS_SNIPPET = (
    f"rows={SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_TOTAL_ROWS} "
    f"dashboard={SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_DASHBOARD_COVERED_ROWS} "
    f"fem={SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_FEM_PROJECTION_ROWS} "
    f"legacy={SPLIT_OWNER_ACCEPTANCE_MATRIX_EXPECTED_LEGACY_ONLY_ROWS}"
)


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    report_path = tmp_path / REPORT_REL
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_split_owner_acceptance_matrix_report(), encoding="utf-8")
    return tmp_path


@pytest.fixture
def mock_pytest_success(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    calls: list[Path] = []

    def _fake_pytest(*, repo_root: Path) -> int:
        calls.append(repo_root)
        return 0

    monkeypatch.setattr(matrix_ops, "run_split_owner_acceptance_matrix_pytest", _fake_pytest)
    monkeypatch.setattr(
        "scripts.refresh_split_owner_acceptance_matrix._ops.run_split_owner_acceptance_matrix_pytest",
        _fake_pytest,
    )
    return calls


def _refresh_main():
    from scripts.refresh_split_owner_acceptance_matrix import main

    return main


def _check_main():
    from scripts.check_split_owner_acceptance_matrix import main

    return main


def test_refresh_default_path_exits_zero_and_runs_pytest(
    temp_repo: Path,
    mock_pytest_success: list[Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = _refresh_main()(["--repo-root", str(temp_repo)])

    assert exit_code == 0
    assert mock_pytest_success == [temp_repo]
    output = capsys.readouterr().out
    assert "[1/3] regenerated docs/audits/BU15_split_owner_acceptance_matrix.md" in output
    assert f"[2/3] split-owner acceptance matrix contract: OK ({EXPECTED_COUNTS_SNIPPET})" in output
    assert "[3/3] split-owner acceptance matrix pytest contract: OK" in output
    assert f"split-owner acceptance matrix refresh: OK ({EXPECTED_COUNTS_SNIPPET})" in output


def test_refresh_write_report_only_writes_report_without_check_or_pytest(
    tmp_path: Path,
    mock_pytest_success: list[Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = _refresh_main()(["--repo-root", str(tmp_path), "--write-report-only"])

    assert exit_code == 0
    assert mock_pytest_success == []
    report_path = tmp_path / REPORT_REL
    assert report_path.is_file()
    assert report_path.read_text(encoding="utf-8") == render_split_owner_acceptance_matrix_report()
    output = capsys.readouterr().out
    assert "[1/1] regenerated docs/audits/BU15_split_owner_acceptance_matrix.md" in output
    assert "split-owner acceptance matrix report: OK (write-report-only)" in output
    assert "contract: OK" not in output


def test_refresh_check_only_validates_without_writing(
    temp_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    mock_pytest_success: list[Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    original_text = (temp_repo / REPORT_REL).read_text(encoding="utf-8")

    def _fail_write(*, repo_root: Path) -> Path:
        raise AssertionError("write_split_owner_acceptance_matrix_report should not run")

    monkeypatch.setattr(matrix_ops, "write_split_owner_acceptance_matrix_report", _fail_write)
    monkeypatch.setattr(
        "scripts.refresh_split_owner_acceptance_matrix._ops.write_split_owner_acceptance_matrix_report",
        _fail_write,
    )

    exit_code = _refresh_main()(["--repo-root", str(temp_repo), "--check-only"])

    assert exit_code == 0
    assert mock_pytest_success == []
    assert (temp_repo / REPORT_REL).read_text(encoding="utf-8") == original_text
    output = capsys.readouterr().out
    assert "[1/1] split-owner acceptance matrix contract: OK" in output
    assert EXPECTED_COUNTS_SNIPPET in output


def test_refresh_skip_pytest_skips_subprocess(
    temp_repo: Path,
    mock_pytest_success: list[Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = _refresh_main()(["--repo-root", str(temp_repo), "--skip-pytest"])

    assert exit_code == 0
    assert mock_pytest_success == []
    output = capsys.readouterr().out
    assert "[1/2] regenerated docs/audits/BU15_split_owner_acceptance_matrix.md" in output
    assert "[2/2] split-owner acceptance matrix contract: OK" in output
    assert "pytest contract" not in output


def test_refresh_repo_root_targets_temp_not_real_repo(
    tmp_path: Path,
    mock_pytest_success: list[Path],
) -> None:
    real_report = REPO_ROOT / REPORT_REL
    real_before = real_report.read_text(encoding="utf-8")

    exit_code = _refresh_main()(["--repo-root", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / REPORT_REL).is_file()
    assert real_report.read_text(encoding="utf-8") == real_before


def test_refresh_contract_failure_exits_nonzero_before_pytest(
    tmp_path: Path,
    mock_pytest_success: list[Path],
    capsys: pytest.CaptureFixture[str],
) -> None:
    stale_dir = tmp_path / "docs" / "audits"
    stale_dir.mkdir(parents=True)
    (stale_dir / "BU15_split_owner_acceptance_matrix.md").write_text("# stale\n", encoding="utf-8")

    exit_code = _refresh_main()(["--repo-root", str(tmp_path), "--check-only"])

    assert exit_code == 1
    assert mock_pytest_success == []
    output = capsys.readouterr()
    assert "[1/1] split-owner acceptance matrix contract: FAIL" in output.out
    assert "contract drift" in output.err
    assert "out of date" in output.err


def test_refresh_pytest_failure_exits_nonzero(
    temp_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        matrix_ops,
        "run_split_owner_acceptance_matrix_pytest",
        lambda *, repo_root: 1,
    )
    monkeypatch.setattr(
        "scripts.refresh_split_owner_acceptance_matrix._ops.run_split_owner_acceptance_matrix_pytest",
        lambda *, repo_root: 1,
    )

    exit_code = _refresh_main()(["--repo-root", str(temp_repo)])

    assert exit_code == 1
    output = capsys.readouterr().out
    assert "[3/3] split-owner acceptance matrix pytest contract: FAIL" in output


def test_check_script_contract_failure_on_missing_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = _check_main()(["--repo-root", str(tmp_path)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "contract: FAIL" in err
    assert "missing report" in err


def test_check_script_contract_failure_on_stale_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    stale_dir = tmp_path / "docs" / "audits"
    stale_dir.mkdir(parents=True)
    (stale_dir / "BU15_split_owner_acceptance_matrix.md").write_text("# stale\n", encoding="utf-8")

    exit_code = _check_main()(["--repo-root", str(tmp_path)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "contract drift" in err
    assert "out of date" in err


def test_ops_missing_report_returns_nonzero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    exit_code, counts = matrix_ops.run_split_owner_acceptance_matrix_check(repo_root=tmp_path)

    assert exit_code == 1
    assert counts is None
    err = capsys.readouterr().err
    assert "missing report" in err


def test_ops_write_report_creates_expected_path(tmp_path: Path) -> None:
    report_path = matrix_ops.write_split_owner_acceptance_matrix_report(repo_root=tmp_path)

    assert report_path == tmp_path / REPORT_REL
    assert report_path.read_text(encoding="utf-8") == render_split_owner_acceptance_matrix_report()


def test_ops_pytest_invocation_uses_contract_marker(
    temp_repo: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def _fake_run(cmd, *, cwd):
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(matrix_ops.subprocess, "run", _fake_run)

    exit_code = matrix_ops.run_split_owner_acceptance_matrix_pytest(repo_root=temp_repo)

    assert exit_code == 0
    assert captured["cwd"] == temp_repo
    cmd = captured["cmd"]
    assert cmd[-4:] == [
        "tests/test_split_owner_acceptance_matrix_contract.py",
        "-q",
        "-m",
        "split_owner_matrix_contract",
    ]
