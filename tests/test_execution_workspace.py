"""Ownership checks for execution-owned temporary directories."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import pytest

from tools.execution_workspace import (
    DEVELOPMENT_TMP,
    OwnedWorkspace,
    WorkspaceOwnershipError,
    claim_publication,
    finish_owned,
)


def _workspace(tmp_path: Path, prefix: str = "owned-") -> OwnedWorkspace:
    return OwnedWorkspace.allocate(tmp_path / "scratch", prefix, allowed_root=tmp_path)


def test_successful_publication_removes_only_the_allocated_directory(tmp_path: Path):
    workspace = _workspace(tmp_path)
    sibling = OwnedWorkspace.allocate(tmp_path / "scratch", "peer-", allowed_root=tmp_path)
    (workspace.root / "pytest").mkdir()
    (workspace.root / "pytest" / "fixture.txt").write_text("scratch", encoding="utf-8")
    claim = claim_publication(tmp_path / "evidence", ("result.json",))
    (tmp_path / "evidence" / "result.json").write_text("{}", encoding="utf-8")
    assert finish_owned(workspace, claim, 0) == 0
    assert not workspace.root.exists()
    assert sibling.root.is_dir()
    assert (tmp_path / "evidence" / "result.json").read_text(encoding="utf-8") == "{}"
    assert not (tmp_path / "evidence" / ".execution-claim").exists()
    sibling.discard()


def test_unpublished_workspace_is_retained_and_reported(tmp_path: Path, capsys):
    workspace = _workspace(tmp_path)
    claim = claim_publication(tmp_path / "evidence", ("result.json",))
    workspace.retain("Publication failed.")
    claim.release_unpublished()
    captured = capsys.readouterr()
    assert str(workspace.root) in captured.err
    assert workspace.root.is_dir()
    assert not (tmp_path / "evidence" / ".execution-claim").exists()
    workspace.discard()


def test_cleanup_failure_after_success_is_reported_and_raised(tmp_path: Path, monkeypatch, capsys):
    workspace = _workspace(tmp_path)
    claim = claim_publication(tmp_path / "evidence", ("result.json",))
    (tmp_path / "evidence" / "result.json").write_text("{}", encoding="utf-8")

    def fail(path):
        raise OSError("injected cleanup failure")

    monkeypatch.setattr("tools.execution_workspace.shutil.rmtree", fail)
    with pytest.raises(OSError, match="injected cleanup failure"):
        finish_owned(workspace, claim, 0)
    captured = capsys.readouterr()
    assert str(workspace.root) in captured.err
    assert workspace.root.is_dir()
    monkeypatch.undo()
    workspace.discard()


def test_cleanup_failure_preserves_a_failed_status(tmp_path: Path, monkeypatch):
    workspace = _workspace(tmp_path)
    claim = claim_publication(tmp_path / "evidence", ("result.json",))
    (tmp_path / "evidence" / "result.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "tools.execution_workspace.shutil.rmtree",
        lambda path: (_ for _ in ()).throw(OSError("injected cleanup failure")),
    )
    assert finish_owned(workspace, claim, 1) == 1
    assert workspace.root.is_dir()
    monkeypatch.undo()
    workspace.discard()


def test_existing_publication_and_a_second_claim_are_refused(tmp_path: Path):
    evidence = tmp_path / "historical"
    evidence.mkdir()
    target = evidence / "result.json"
    target.write_text("historical", encoding="utf-8")
    with pytest.raises(FileExistsError):
        claim_publication(evidence, ("result.json",))
    assert target.read_text(encoding="utf-8") == "historical"
    assert not (evidence / ".execution-claim").exists()

    fresh = tmp_path / "fresh"
    first = claim_publication(fresh, ("result.json",))
    with pytest.raises(FileExistsError, match="already claimed"):
        claim_publication(fresh, ("result.json",))
    assert first.path.is_file()
    first.release_unpublished()


def test_concurrent_claims_have_one_owner(tmp_path: Path):
    evidence = tmp_path / "shared"
    barrier = threading.Barrier(2)
    outcomes = []

    def attempt():
        barrier.wait(timeout=10)
        try:
            claim_publication(evidence, ("result.json",))
            outcomes.append("owned")
        except FileExistsError:
            outcomes.append("refused")

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert sorted(outcomes) == ["owned", "refused"]
    assert (evidence / ".execution-claim").is_file()


def test_discard_refuses_a_reported_reparse_point(tmp_path: Path, monkeypatch):
    workspace = _workspace(tmp_path)
    monkeypatch.setattr("tools.execution_workspace._reparse", lambda path: True)
    with pytest.raises(WorkspaceOwnershipError, match="reparse"):
        workspace.discard()
    monkeypatch.undo()
    assert workspace.root.is_dir()
    workspace.discard()


def test_reparse_point_and_foreign_paths_are_not_removed(tmp_path: Path):
    workspace = _workspace(tmp_path)
    payload = workspace.root / "payload.txt"
    payload.write_text("keep", encoding="utf-8")
    link = tmp_path / "scratch" / "link-owned"
    try:
        os.symlink(workspace.root, link, target_is_directory=True)
    except OSError as exc:
        workspace.discard()
        pytest.skip(f"directory symlink is unavailable: {exc}")
    foreign = OwnedWorkspace(link, workspace.parent, workspace.boundary)
    with pytest.raises(WorkspaceOwnershipError):
        foreign.discard()
    assert payload.read_text(encoding="utf-8") == "keep"
    outside = tmp_path / "outside"
    outside.mkdir()
    with pytest.raises(WorkspaceOwnershipError):
        OwnedWorkspace.allocate(outside, "no-", allowed_root=tmp_path / "scratch")
    assert not any(outside.iterdir())
    workspace.discard()


def test_preexisting_directory_with_the_runner_prefix_survives(tmp_path: Path):
    parent = tmp_path / "scratch"
    parent.mkdir()
    historical = parent / "case-1-historical"
    historical.mkdir()
    (historical / "keep.txt").write_text("historical", encoding="utf-8")
    workspace = OwnedWorkspace.allocate(parent, "case-1-", allowed_root=tmp_path)
    assert workspace.root.name.startswith("case-1-")
    assert workspace.root != historical
    workspace.discard()
    assert (historical / "keep.txt").read_text(encoding="utf-8") == "historical"
    assert not workspace.root.exists()


def test_neighboring_directory_survives_cleanup(tmp_path: Path):
    workspace = _workspace(tmp_path)
    neighbor = workspace.parent / "neighbor-evidence"
    neighbor.mkdir()
    (neighbor / "keep.txt").write_text("neighbor", encoding="utf-8")
    workspace.discard()
    assert (neighbor / "keep.txt").read_text(encoding="utf-8") == "neighbor"
    assert not workspace.root.exists()


def test_failed_allocation_does_not_remove_a_guessed_path(tmp_path: Path, monkeypatch):
    parent = tmp_path / "scratch"
    parent.mkdir()
    guessed = parent / "case-1-guessed"
    guessed.mkdir()
    (guessed / "keep.txt").write_text("keep", encoding="utf-8")

    def fail(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr("tools.execution_workspace.tempfile.mkdtemp", fail)
    with pytest.raises(OSError, match="disk full"):
        OwnedWorkspace.allocate(parent, "case-1-", allowed_root=tmp_path)
    assert (guessed / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_failed_status_removes_only_a_published_workspace(tmp_path: Path):
    workspace = _workspace(tmp_path)
    evidence = tmp_path / "evidence"
    claim = claim_publication(evidence, ("result.json",))
    (evidence / "result.json").write_text('{"failed": 1}', encoding="utf-8")
    assert finish_owned(workspace, claim, 1) == 1
    assert not workspace.root.exists()
    assert (evidence / "result.json").read_text(encoding="utf-8") == '{"failed": 1}'


def test_absent_publication_keeps_the_workspace(tmp_path: Path, capsys):
    workspace = _workspace(tmp_path)
    claim = claim_publication(tmp_path / "evidence", ("result.json",))
    with pytest.raises(WorkspaceOwnershipError, match="publication"):
        finish_owned(workspace, claim, 0)
    captured = capsys.readouterr()
    assert str(workspace.root) in captured.err
    assert workspace.root.is_dir()
    assert finish_owned(workspace, claim, 1) == 1
    assert workspace.root.is_dir()
    workspace.discard()


def test_concurrent_workers_cannot_remove_each_others_workspace(tmp_path: Path):
    parent = tmp_path / "scratch"
    barrier = threading.Barrier(2)
    created: list[OwnedWorkspace] = []

    def work():
        barrier.wait(timeout=10)
        workspace = OwnedWorkspace.allocate(parent, "worker-", allowed_root=tmp_path)
        (workspace.root / "marker.txt").write_text("owned", encoding="utf-8")
        created.append(workspace)
        barrier.wait(timeout=10)

    threads = [threading.Thread(target=work) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert len(created) == 2
    first, second = created
    stolen = OwnedWorkspace(second.root, second.parent, second.boundary, owner_token="0" * 64)
    with pytest.raises(WorkspaceOwnershipError):
        stolen.discard()
    first.discard()
    assert not first.root.exists()
    assert (second.root / "marker.txt").read_text(encoding="utf-8") == "owned"
    second.discard()
    assert not second.root.exists()


def test_replaced_directory_is_not_removed(tmp_path: Path):
    workspace = _workspace(tmp_path)
    path = workspace.root
    shutil.rmtree(path)
    path.mkdir()
    (path / "decoy.txt").write_text("keep", encoding="utf-8")
    with pytest.raises(WorkspaceOwnershipError, match="owner record"):
        workspace.discard()
    assert (path / "decoy.txt").read_text(encoding="utf-8") == "keep"


def _directory_redirection(link: Path, target: Path) -> str | None:
    try:
        os.symlink(target, link, target_is_directory=True)
        return "symlink"
    except OSError:
        pass
    completed = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode == 0:
        return "junction"
    return None


def test_cleanup_does_not_follow_a_directory_redirection(tmp_path: Path):
    protected = tmp_path / "protected"
    protected.mkdir()
    (protected / "marker.txt").write_text("keep", encoding="utf-8")
    workspace = _workspace(tmp_path)
    link = workspace.root / "jump"
    kind = _directory_redirection(link, protected)
    if kind is None:
        workspace.discard()
        pytest.skip("directory symlink and junction are unavailable")
    with pytest.raises(WorkspaceOwnershipError, match="reparse"):
        workspace.discard()
    assert (protected / "marker.txt").read_text(encoding="utf-8") == "keep"
    assert workspace.root.is_dir()
    link.unlink() if kind == "symlink" else os.rmdir(link)
    workspace.discard()
    assert not workspace.root.exists()
    assert (protected / "marker.txt").is_file()


def _pytest_run_names() -> set[str]:
    if not DEVELOPMENT_TMP.is_dir():
        return set()
    return {path.name for path in DEVELOPMENT_TMP.glob("pytest-run-*") if path.is_dir()}


def test_default_pytest_session_removes_only_the_workspace_it_created(tmp_path: Path):
    sample = tmp_path / "test_sample.py"
    sample.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    before = _pytest_run_names()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(sample), "-p", "no:cacheprovider", "-q", "--tb=short"],
        cwd=Path(".").resolve(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert _pytest_run_names() == before


def test_explicit_basetemp_does_not_delete_a_neighbor(tmp_path: Path):
    sample = tmp_path / "test_sample.py"
    sample.write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    base = tmp_path / "explicit-base"
    base.mkdir()
    (base / "marker.txt").write_text("base", encoding="utf-8")
    neighbor = tmp_path / "neighbor"
    neighbor.mkdir()
    (neighbor / "keep.txt").write_text("keep", encoding="utf-8")
    before = _pytest_run_names()
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", str(sample), f"--basetemp={base}", "-p", "no:cacheprovider", "-q", "--tb=short"],
        cwd=Path(".").resolve(),
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert base.is_dir()
    assert (neighbor / "keep.txt").read_text(encoding="utf-8") == "keep"
    assert _pytest_run_names() == before


def test_historical_social_directories_do_not_qualify_for_deletion():
    inventory = Path("artifacts/at_fg_03b_r1/baseline/social-children.json")
    payload = json.loads(inventory.read_text(encoding="utf-8"))
    root = DEVELOPMENT_TMP / "social-reconciliation"
    checked = 0
    for child in payload["children"]:
        if child.get("reparse_or_file"):
            continue
        path = root / child["name"]
        assert path.is_dir()
        reason = OwnedWorkspace(path, root, DEVELOPMENT_TMP).ownership_failure()
        assert reason
        assert path.is_dir()
        checked += 1
    assert checked > 0


def test_allocation_outside_development_tmp_is_refused():
    outside = Path(tempfile.mkdtemp(prefix="at-fg-03b-outside-"))
    try:
        with pytest.raises(WorkspaceOwnershipError):
            OwnedWorkspace.allocate(outside / "scratch", "repo-")
        assert not (outside / "scratch").exists()
    finally:
        shutil.rmtree(outside)
