"""Ownership for a temporary directory this process just created.

Callers may remove only a directory returned by ``allocate``. A directory name,
a prefix, an age, or a path under ``development/tmp`` is not ownership.
``allocate`` writes a secret that stays in this object. ``discard`` deletes
only when that secret still matches the exact directory.

The check and the deletion are not one filesystem transaction. A directory
replaced after the check and before ``rmtree`` can still race. This module
fails closed when the check itself is uncertain, and it does not claim
race-free deletion.
"""

from __future__ import annotations

import os
import secrets
import shutil
import stat
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_TMP = REPO_ROOT / "development" / "tmp"
OUTPUT_ENV = "ASHEN_REGRESSION_OUTPUT"
OWNER_FILE = ".ashen-execution-owner"


class WorkspaceOwnershipError(OSError):
    """The path is not an execution-owned workspace that this process may remove."""


def resolve_evidence_directory(default: Path) -> Path:
    """Return a caller-selected evidence directory, or the historical default."""

    override = os.environ.get(OUTPUT_ENV, "").strip()
    if not override:
        return default
    path = Path(override)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


class PublicationClaim:
    """Exclusive reservation for one evidence directory."""

    def __init__(self, path: Path, directory: Path, names: tuple[str, ...]) -> None:
        self.path = path
        self.directory = directory
        self.names = names

    def release_unpublished(self) -> None:
        if any((self.directory / name).exists() for name in self.names):
            return
        self.path.unlink(missing_ok=True)

    def release_after_publication(self) -> None:
        self.path.unlink(missing_ok=True)


def claim_publication(directory: Path, names: tuple[str, ...]) -> PublicationClaim:
    """Reserve ``directory`` without replacing publication files that already exist."""

    directory = Path(directory)
    existing = [directory / name for name in names if (directory / name).exists()]
    if existing:
        raise FileExistsError(
            f"Refusing to overwrite {existing[0]}. "
            f"Set {OUTPUT_ENV} to a fresh directory."
        )
    directory.mkdir(parents=True, exist_ok=True)
    claim = directory / ".execution-claim"
    try:
        descriptor = os.open(claim, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise FileExistsError(f"Output {directory} is already claimed by another execution.") from exc
    try:
        os.write(descriptor, f"{os.getpid()}\n".encode("ascii"))
    finally:
        os.close(descriptor)
    existing = [directory / name for name in names if (directory / name).exists()]
    if existing:
        claim.unlink(missing_ok=True)
        raise FileExistsError(
            f"Refusing to overwrite {existing[0]}. "
            f"Set {OUTPUT_ENV} to a fresh directory."
        )
    return PublicationClaim(claim, directory, names)


def _reparse(path: Path) -> bool:
    try:
        metadata = path.lstat()
    except OSError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _inside(path: Path, boundary: Path) -> bool:
    return path == boundary or boundary in path.parents


def _nested_reparse(root: Path) -> str | None:
    """Return a child reparse point. Do not descend through one."""

    pending = [root]
    while pending:
        current = pending.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            return str(current)
        for entry in entries:
            path = Path(entry.path)
            if _reparse(path):
                return str(path)
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError:
                return str(path)
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(path)
    return None


class OwnedWorkspace:
    """A unique directory allocated under an allowed temporary boundary."""

    def __init__(self, root: Path, parent: Path, boundary: Path, owner_token: str | None = None) -> None:
        self.root = root
        self.parent = parent
        self.boundary = boundary
        self.owner_token = owner_token

    @classmethod
    def allocate(cls, parent: Path, prefix: str, *, allowed_root: Path | None = None) -> OwnedWorkspace:
        boundary = (allowed_root or DEVELOPMENT_TMP).resolve()
        resolved_parent = Path(parent).resolve()
        if not _inside(resolved_parent, boundary) or (parent.exists() and _reparse(parent)):
            raise WorkspaceOwnershipError(f"Refusing to allocate outside {boundary}: {parent}")
        resolved_parent.mkdir(parents=True, exist_ok=True)
        if _reparse(resolved_parent):
            raise WorkspaceOwnershipError(f"Refusing to allocate through reparse point {resolved_parent}")
        root = Path(tempfile.mkdtemp(prefix=prefix, dir=resolved_parent)).resolve()
        token = secrets.token_hex(32)
        descriptor = os.open(root / OWNER_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        try:
            os.write(descriptor, token.encode("ascii"))
        finally:
            os.close(descriptor)
        return cls(root, resolved_parent, boundary, token)

    def ownership_failure(self) -> str | None:
        """Return why this object must not delete its directory, or None when it may."""

        if not self.owner_token:
            return "this execution has no creation token for the directory"
        root = self.root
        if _reparse(root):
            return f"directory is a reparse point: {root}"
        if _reparse(self.parent):
            return f"parent is a reparse point: {self.parent}"
        try:
            resolved = root.resolve()
        except OSError as exc:
            return f"directory cannot be resolved: {exc}"
        if resolved != root:
            return f"directory path changed: {root}"
        if resolved.parent != self.parent or not _inside(resolved, self.boundary):
            return f"directory is outside {self.parent}"
        if not resolved.is_dir():
            return "path is not a directory"
        token_path = resolved / OWNER_FILE
        if _reparse(token_path):
            return "owner record is a reparse point"
        try:
            metadata = token_path.lstat()
        except OSError as exc:
            return f"owner record is missing: {exc}"
        if not stat.S_ISREG(metadata.st_mode):
            return "owner record is not a regular file"
        try:
            recorded = token_path.read_text(encoding="ascii")
        except OSError as exc:
            return f"owner record is unreadable: {exc}"
        if len(recorded) != len(self.owner_token) or not secrets.compare_digest(recorded, self.owner_token):
            return "owner record does not match this execution"
        redirected = _nested_reparse(resolved)
        if redirected:
            return f"directory contains a reparse point: {redirected}"
        return None

    def discard(self) -> None:
        """Remove this workspace. Refuse a path this execution cannot prove it created."""

        reason = self.ownership_failure()
        if reason:
            raise WorkspaceOwnershipError(f"Refusing to remove {self.root}: {reason}")
        shutil.rmtree(self.root)

    def retain(self, reason: str) -> None:
        print(f"{reason} Scratch retained at {self.root}", file=sys.stderr)


def finish_owned(workspace: OwnedWorkspace, claim: PublicationClaim, status: int) -> int:
    """Remove a published workspace. Keep a non-zero status if cleanup also fails."""

    if not any((claim.directory / name).is_file() for name in claim.names):
        workspace.retain("Refusing cleanup because required publication files are absent.")
        if status != 0:
            return status
        raise WorkspaceOwnershipError(
            f"Refusing to remove {workspace.root}: required publication files are absent"
        )
    try:
        workspace.discard()
    except OSError as exc:
        print(f"Could not clean execution workspace {workspace.root}: {exc}", file=sys.stderr)
        claim.release_after_publication()
        if status != 0:
            return status
        raise
    claim.release_after_publication()
    return status
