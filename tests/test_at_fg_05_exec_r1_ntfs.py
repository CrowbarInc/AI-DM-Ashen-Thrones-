"""Isolated NTFS deletion tests for AT-FG-05-EXEC-R1.

Fixtures live under the pytest workspace in development/tmp and carry the R1
owner marker. They are not historical artifact or campaign paths.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _load(name: str):
    path = REPO / "artifacts" / "at_fg_05_exec_r1" / name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ntfs = _load("ntfs_disposition.py")
continuation = _load("continuation.py")


@pytest.fixture
def owned(tmp_path: Path):
    root = continuation.allocate_fixture(tmp_path)
    yield root
    if root.exists():
        continuation.discard_fixture(root)


def _identity(path: Path):
    found = ntfs.lookup_nofollow(path)
    assert found.state == ntfs.EXISTS_VERIFIED
    return found.identity


def test_ordinary_file_deletion(owned: Path):
    target = owned / "note.txt"
    target.write_text("alpha", encoding="utf-8")
    outcome = ntfs.delete_exact(
        target, root=owned, expected_identity=_identity(target), expected_kind="file",
        expected_sha256="0" * 64, expected_size=5,
    )
    assert outcome.state == ntfs.DELETE_FAILED
    assert "SHA-256" in outcome.note
    assert target.read_text(encoding="utf-8") == "alpha"
    outcome = ntfs.delete_exact(
        target, root=owned, expected_identity=_identity(target), expected_kind="file",
        expected_size=5,
    )
    assert outcome.state == ntfs.DELETED_VERIFIED
    assert ntfs.lookup_nofollow(target).state == ntfs.MISSING


def test_ordinary_file_hash_gate(owned: Path):
    target = owned / "hashed.txt"
    payload = b"exact-bytes"
    target.write_bytes(payload)
    import hashlib
    digest = hashlib.sha256(payload).hexdigest()
    outcome = ntfs.delete_exact(
        target, root=owned, expected_identity=_identity(target), expected_kind="file",
        expected_sha256=digest, expected_size=len(payload),
    )
    assert outcome.state == ntfs.DELETED_VERIFIED
    assert not target.exists()


def test_ordinary_empty_directory(owned: Path):
    target = owned / "empty"
    target.mkdir()
    outcome = ntfs.delete_exact(target, root=owned, expected_identity=_identity(target), expected_kind="directory")
    assert outcome.state == ntfs.DELETED_VERIFIED
    assert ntfs.lookup_nofollow(target).state == ntfs.MISSING


def test_nested_directory_deletion(owned: Path):
    leaf = owned / "a" / "b"
    leaf.mkdir(parents=True)
    note = leaf / "c.txt"
    note.write_text("nested", encoding="utf-8")
    file_result = ntfs.delete_exact(note, root=owned, expected_identity=_identity(note), expected_kind="file", expected_size=6)
    inner = ntfs.delete_exact(leaf, root=owned, expected_identity=_identity(leaf), expected_kind="directory")
    outer = ntfs.delete_exact(owned / "a", root=owned, expected_identity=_identity(owned / "a"), expected_kind="directory")
    assert file_result.state == inner.state == outer.state == ntfs.DELETED_VERIFIED
    assert ntfs.lookup_nofollow(owned / "a").state == ntfs.MISSING


def test_delayed_disappearance(owned: Path):
    target = owned / "delayed.txt"
    target.write_text("wait", encoding="utf-8")
    identity = _identity(target)
    holder, error = ntfs._open(target, ntfs.FILE_READ_ATTRIBUTES, directory=False)
    assert holder is not None, error
    closed = {"done": False}

    def release_during_wait(path: Path):
        found = ntfs.lookup_nofollow(path)
        if not closed["done"] and (found.delete_pending or found.state == ntfs.DELETE_PENDING):
            ntfs.KERNEL.CloseHandle(holder)
            closed["done"] = True
        return found

    try:
        outcome = ntfs.delete_exact(
            target, root=owned, expected_identity=identity, expected_kind="file", expected_size=4,
            delays=(0.0, 0.05, 0.10, 0.20, 0.40), lookup=release_during_wait,
        )
        assert outcome.state == ntfs.DELETED_VERIFIED
        assert outcome.attempts >= 2
    finally:
        if not closed["done"]:
            ntfs.KERNEL.CloseHandle(holder)


def test_open_handle_stays_pending(owned: Path):
    target = owned / "held.txt"
    target.write_text("held", encoding="utf-8")
    identity = _identity(target)
    holder, error = ntfs._open(target, ntfs.FILE_READ_ATTRIBUTES, directory=False)
    assert holder is not None, error
    try:
        outcome = ntfs.delete_exact(
            target, root=owned, expected_identity=identity, expected_kind="file", expected_size=4,
            delays=(0.0, 0.02, 0.02),
        )
        assert outcome.state == ntfs.DELETE_PENDING
        assert outcome.state != ntfs.DELETED_VERIFIED
        assert ntfs.lookup_nofollow(target).delete_pending or ntfs.lookup_nofollow(target).state == ntfs.DELETE_PENDING
    finally:
        ntfs.KERNEL.CloseHandle(holder)
    finished = ntfs.confirm_absence(target, identity, delays=(0.0, 0.05, 0.10, 0.20))
    assert finished.state == ntfs.DELETED_VERIFIED


def test_missing_target_is_classified(owned: Path):
    target = owned / "absent.txt"
    outcome = ntfs.delete_exact(target, root=owned, expected_identity=["0", "0"], expected_kind="file")
    assert outcome.state == ntfs.MISSING


def test_changed_file_identity_is_refused(owned: Path):
    target = owned / "swap.txt"
    target.write_text("first", encoding="utf-8")
    original = _identity(target)
    target.unlink()
    target.write_text("second", encoding="utf-8")
    outcome = ntfs.delete_exact(target, root=owned, expected_identity=original, expected_kind="file", expected_size=5)
    assert outcome.state == ntfs.IDENTITY_MISMATCH
    assert target.read_text(encoding="utf-8") == "second"


def test_unexpected_file_blocks_directory_deletion(owned: Path):
    directory = owned / "box"
    directory.mkdir()
    extra = directory / "extra.txt"
    extra.write_text("stay", encoding="utf-8")
    outcome = ntfs.delete_exact(directory, root=owned, expected_identity=_identity(directory), expected_kind="directory")
    assert outcome.state == ntfs.UNEXPECTED_OBJECT
    assert extra.read_text(encoding="utf-8") == "stay"


def test_junction_is_refused(owned: Path):
    real = owned / "real"
    real.mkdir()
    (real / "kept.txt").write_text("kept", encoding="utf-8")
    link = owned / "link"
    completed = os.system(f'cmd /c mklink /J "{link}" "{real}"')
    assert completed == 0
    outcome = ntfs.delete_exact(link, root=owned, expected_identity=["0", "0"], expected_kind="directory")
    assert outcome.state == ntfs.UNEXPECTED_OBJECT
    assert (real / "kept.txt").read_text(encoding="utf-8") == "kept"
    assert link.exists()


def test_unauthorized_historical_path_is_refused(owned: Path):
    protected = REPO / "artifacts" / "at_opt_04" / "optimized_measurement.json"
    before = protected.read_bytes()
    outcome = ntfs.delete_exact(protected, root=owned, expected_identity=["0", "0"], expected_kind="file")
    assert outcome.state == ntfs.REFUSED
    assert protected.read_bytes() == before


def test_partial_interruption_writes_a_durable_record(owned: Path):
    first = owned / "one.txt"
    second = owned / "two.txt"
    first.write_text("one", encoding="utf-8")
    second.write_text("two", encoding="utf-8")
    outcome = ntfs.delete_exact(first, root=owned, expected_identity=_identity(first), expected_kind="file", expected_size=3)
    continuation.append_recovery(owned, {"path": "one.txt", "state": outcome.state, "interrupted_before": "two.txt"})
    assert outcome.state == ntfs.DELETED_VERIFIED
    saved = json.loads((owned / "recovery.jsonl").read_text(encoding="utf-8"))
    assert saved["interrupted_before"] == "two.txt"
    assert second.read_text(encoding="utf-8") == "two"


def test_path_replaced_after_absence_is_not_deleted(owned: Path):
    target = owned / "replaced.txt"
    target.write_text("old", encoding="utf-8")
    original = _identity(target)
    removed = ntfs.delete_exact(target, root=owned, expected_identity=original, expected_kind="file", expected_size=3)
    assert removed.state == ntfs.DELETED_VERIFIED
    target.write_text("new-object", encoding="utf-8")
    outcome = ntfs.confirm_absence(target, original, delays=(0.0,))
    assert outcome.state == ntfs.IDENTITY_MISMATCH
    assert target.read_text(encoding="utf-8") == "new-object"


def test_mocked_replacement_during_confirmation_does_not_request_another_delete(owned: Path):
    target = owned / "mocked.txt"
    target.write_text("body", encoding="utf-8")
    identity = _identity(target)
    calls = {"lookups": 0}

    def lookup(path: Path):
        calls["lookups"] += 1
        if calls["lookups"] == 1:
            return ntfs.lookup_nofollow(path)
        return ntfs.Lookup(ntfs.EXISTS_VERIFIED, identity=["9", "different"], kind="file", note="injected replacement")

    outcome = ntfs.delete_exact(
        target, root=owned, expected_identity=identity, expected_kind="file", expected_size=4,
        delays=(0.0,), lookup=lookup,
    )
    assert outcome.state == ntfs.IDENTITY_MISMATCH
    assert "replacement not touched" in outcome.note
    # The injected lookup hides the real file. A second real lookup must still
    # see either absence or the original object, and this test does not delete
    # a second time. The mock itself is not a real replacement success.
    assert calls["lookups"] >= 2


def test_historical_resume_refuses_without_deleting(owned: Path):
    partial = REPO / "artifacts" / "pr_play_72" / "boundary_tmp" / "test_endpoint_lockout_matrix_a0"
    before = partial.exists()
    result = continuation.resume_historical({"continuation_authorized": True})
    assert result["status"] == "REFUSED"
    assert result["historical_deletion_performed"] is False
    assert partial.exists() is before
    refused = continuation.resume_historical({"continuation_authorized": False})
    assert refused["reason"] == "continuation_authorized is false"
