"""NTFS deletion verification for AT-FG-05-EXEC-R1.

The historical executor treated a successful FileDispositionInfo call followed
by an immediate path-existence hit as failure. On NTFS that call marks the
object delete-pending. The name remains visible until the last handle closes.
This module closes the disposition handle, then distinguishes pending deletion
from a surviving or replaced object. A bounded retry is not a success.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
import stat
import time
from ctypes import wintypes
from dataclasses import dataclass, field
from pathlib import Path

EXECUTOR_VERSION = "AT-FG-05-EXEC-R1.1"
API_NAME = "SetFileInformationByHandle/FileDispositionInfo"
FILE_DISPOSITION_INFO_CLASS = 4
FILE_STANDARD_INFO_CLASS = 1
FILE_ID_INFO_CLASS = 18
GENERIC_READ = 0x80000000
FILE_READ_ATTRIBUTES = 0x80
DELETE_ACCESS = 0x00010000
FILE_SHARE_ALL = 0x1 | 0x2 | 0x4
OPEN_EXISTING = 3
FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
FILE_ATTRIBUTE_READONLY = 0x1
FILE_ATTRIBUTE_REPARSE_POINT = 0x400
FILE_ATTRIBUTE_DIRECTORY = 0x10
ERROR_FILE_NOT_FOUND = 2
ERROR_PATH_NOT_FOUND = 3
ERROR_ACCESS_DENIED = 5
ERROR_DELETE_PENDING = 303
INVALID_HANDLE = wintypes.HANDLE(-1).value
DEFAULT_DELAYS = (0.0, 0.05, 0.10, 0.20, 0.40, 0.80)

EXISTS_VERIFIED = "EXISTS-VERIFIED"
DELETE_REQUESTED = "DELETE-REQUESTED"
DELETE_PENDING = "DELETE-PENDING"
DELETED_VERIFIED = "DELETED-VERIFIED"
DELETE_FAILED = "DELETE-FAILED"
IDENTITY_MISMATCH = "IDENTITY-MISMATCH"
UNEXPECTED_OBJECT = "UNEXPECTED-OBJECT"
MISSING = "MISSING"
REFUSED = "REFUSED"

KERNEL = ctypes.WinDLL("kernel32", use_last_error=True)
KERNEL.CreateFileW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
    wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
]
KERNEL.CreateFileW.restype = wintypes.HANDLE
KERNEL.GetFileInformationByHandleEx.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
]
KERNEL.GetFileInformationByHandleEx.restype = wintypes.BOOL
KERNEL.SetFileInformationByHandle.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD,
]
KERNEL.SetFileInformationByHandle.restype = wintypes.BOOL
KERNEL.SetFileAttributesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD]
KERNEL.SetFileAttributesW.restype = wintypes.BOOL
KERNEL.ReadFile.argtypes = [
    wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
]
KERNEL.ReadFile.restype = wintypes.BOOL
KERNEL.CloseHandle.argtypes = [wintypes.HANDLE]
KERNEL.CloseHandle.restype = wintypes.BOOL


class StandardInfo(ctypes.Structure):
    _fields_ = [
        ("allocated", ctypes.c_longlong),
        ("length", ctypes.c_longlong),
        ("links", wintypes.DWORD),
        ("pending", wintypes.BOOLEAN),
        ("directory", wintypes.BOOLEAN),
    ]


class FileId(ctypes.Structure):
    _fields_ = [("volume_serial", ctypes.c_uint64), ("file_id", ctypes.c_ubyte * 16)]


class DispositionInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("delete_file", ctypes.c_ubyte)]


@dataclass
class Lookup:
    state: str
    identity: list | None = None
    kind: str | None = None
    delete_pending: bool = False
    size: int | None = None
    attributes: int | None = None
    winerror: int | None = None
    note: str = ""


@dataclass
class Outcome:
    state: str
    path: str
    expected_identity: list | None = None
    observed_identity: list | None = None
    kind: str | None = None
    delete_pending: bool = False
    attempts: int = 0
    api: str = API_NAME
    winerror: int | None = None
    note: str = ""
    phases: list = field(default_factory=list)

    def as_dict(self):
        return {
            "api": self.api,
            "attempts": self.attempts,
            "delete_pending": self.delete_pending,
            "expected_identity": self.expected_identity,
            "kind": self.kind,
            "note": self.note,
            "observed_identity": self.observed_identity,
            "path": self.path,
            "phases": list(self.phases),
            "state": self.state,
            "winerror": self.winerror,
        }


def win_path(path: Path) -> str:
    return "\\\\?\\" + os.path.abspath(path)


def same_identity(left, right) -> bool:
    return left is not None and right is not None and list(left) == list(right)


def contained(root: Path, path: Path) -> bool:
    root_abs = Path(os.path.abspath(root))
    path_abs = Path(os.path.abspath(path))
    try:
        path_abs.relative_to(root_abs)
    except ValueError:
        return False
    return True


def _open(path: Path, access: int, directory: bool):
    flags = FILE_FLAG_OPEN_REPARSE_POINT
    if directory:
        flags |= FILE_FLAG_BACKUP_SEMANTICS
    handle = KERNEL.CreateFileW(win_path(path), access, FILE_SHARE_ALL, None, OPEN_EXISTING, flags, None)
    if handle == INVALID_HANDLE:
        return None, ctypes.get_last_error()
    return handle, 0


def _read_handle(handle) -> Lookup:
    standard, identity = StandardInfo(), FileId()
    if not KERNEL.GetFileInformationByHandleEx(handle, FILE_STANDARD_INFO_CLASS, ctypes.byref(standard), ctypes.sizeof(standard)):
        return Lookup("ERROR", winerror=ctypes.get_last_error(), note="FileStandardInfo failed")
    if not KERNEL.GetFileInformationByHandleEx(handle, FILE_ID_INFO_CLASS, ctypes.byref(identity), ctypes.sizeof(identity)):
        return Lookup("ERROR", winerror=ctypes.get_last_error(), note="FileIdInfo failed")
    kind = "directory" if standard.directory else "file"
    return Lookup(
        EXISTS_VERIFIED,
        identity=[int(identity.volume_serial), bytes(identity.file_id).hex()],
        kind=kind,
        delete_pending=bool(standard.pending),
        size=int(standard.length),
    )


def lookup_nofollow(path: Path) -> Lookup:
    """Fresh no-follow lookup. Does not set a delete disposition."""
    try:
        metadata = os.lstat(win_path(path))
    except FileNotFoundError:
        return Lookup(MISSING, note="path is absent")
    except OSError as exc:
        winerror = getattr(exc, "winerror", None)
        if winerror in {ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND}:
            return Lookup(MISSING, winerror=winerror, note="path is absent")
        return Lookup("ERROR", winerror=winerror, note=str(exc))
    attributes = int(getattr(metadata, "st_file_attributes", 0))
    if attributes & FILE_ATTRIBUTE_REPARSE_POINT:
        return Lookup(
            UNEXPECTED_OBJECT,
            kind="reparse",
            attributes=attributes,
            note="symlink or junction; deletion refused",
        )
    directory = stat.S_ISDIR(metadata.st_mode) or bool(attributes & FILE_ATTRIBUTE_DIRECTORY)
    handle, error = _open(path, FILE_READ_ATTRIBUTES, directory=True)
    if handle is None:
        if error in {ERROR_FILE_NOT_FOUND, ERROR_PATH_NOT_FOUND}:
            return Lookup(MISSING, winerror=error, note="path disappeared during lookup")
        if error in {ERROR_DELETE_PENDING, ERROR_ACCESS_DENIED}:
            return Lookup(
                DELETE_PENDING,
                kind="directory" if directory else "file",
                delete_pending=True,
                winerror=error,
                note="name is visible and the object rejected a fresh open",
            )
        return Lookup("ERROR", winerror=error, note=f"CreateFileW failed {error}")
    try:
        found = _read_handle(handle)
    finally:
        KERNEL.CloseHandle(handle)
    found.attributes = attributes
    if found.state == EXISTS_VERIFIED and found.delete_pending:
        found.state = DELETE_PENDING
        found.note = "FileStandardInfo.DeletePending is set"
    return found


def _hash_handle(handle) -> tuple[str | None, int | None]:
    hasher = hashlib.sha256()
    buffer = ctypes.create_string_buffer(1024 * 1024)
    read = wintypes.DWORD()
    while True:
        ok = KERNEL.ReadFile(handle, buffer, len(buffer), ctypes.byref(read), None)
        if not ok:
            return None, ctypes.get_last_error()
        if read.value == 0:
            return hasher.hexdigest(), None
        hasher.update(buffer.raw[: read.value])


def _confirm(path: Path, expected_identity, delays, lookup) -> Outcome:
    last = None
    for attempt, delay in enumerate(delays, start=1):
        if delay:
            time.sleep(delay)
        found = lookup(path)
        last = found
        if found.state == MISSING:
            again = lookup(path)
            if again.state == MISSING:
                return Outcome(
                    DELETED_VERIFIED, str(path), expected_identity, None,
                    attempts=attempt, note="absent on two consecutive no-follow lookups",
                    phases=[DELETE_REQUESTED, DELETED_VERIFIED],
                )
            if not same_identity(again.identity, expected_identity):
                return Outcome(
                    IDENTITY_MISMATCH, str(path), expected_identity, again.identity,
                    kind=again.kind, attempts=attempt,
                    note="path disappeared and a different object appeared; replacement not touched",
                    phases=[DELETE_REQUESTED, IDENTITY_MISMATCH],
                )
            return Outcome(
                DELETE_FAILED, str(path), expected_identity, again.identity,
                kind=again.kind, attempts=attempt,
                note="path disappeared and the same identity returned",
                phases=[DELETE_REQUESTED, DELETE_FAILED],
            )
        if found.state == UNEXPECTED_OBJECT:
            return Outcome(
                UNEXPECTED_OBJECT, str(path), expected_identity, found.identity,
                kind=found.kind, attempts=attempt, note=found.note or "unexpected object",
                phases=[DELETE_REQUESTED, UNEXPECTED_OBJECT],
            )
        if found.identity is not None and not same_identity(found.identity, expected_identity):
            return Outcome(
                IDENTITY_MISMATCH, str(path), expected_identity, found.identity,
                kind=found.kind, attempts=attempt,
                note="a different filesystem identity is at the path; replacement not touched",
                phases=[DELETE_REQUESTED, IDENTITY_MISMATCH],
            )
        if found.delete_pending or found.state == DELETE_PENDING:
            continue
        return Outcome(
            DELETE_FAILED, str(path), expected_identity, found.identity,
            kind=found.kind, delete_pending=False, attempts=attempt, winerror=found.winerror,
            note="object is still present and is not delete-pending",
            phases=[DELETE_REQUESTED, DELETE_FAILED],
        )
    pending = bool(last and (last.delete_pending or last.state == DELETE_PENDING))
    return Outcome(
        DELETE_PENDING if pending else DELETE_FAILED,
        str(path), expected_identity, None if last is None else last.identity,
        kind=None if last is None else last.kind,
        delete_pending=pending,
        attempts=len(delays),
        winerror=None if last is None else last.winerror,
        note="bounded retries ended while the object was still delete-pending" if pending else "bounded retries ended without verified absence",
        phases=[DELETE_REQUESTED, DELETE_PENDING if pending else DELETE_FAILED],
    )


def delete_exact(
    path: Path,
    *,
    root: Path,
    expected_identity,
    expected_kind: str,
    expected_sha256: str | None = None,
    expected_size: int | None = None,
    delays=DEFAULT_DELAYS,
    lookup=lookup_nofollow,
) -> Outcome:
    """Delete one already-identified file or empty directory inside ``root``.

    ``lookup`` exists so a test can show a replacement during confirmation.
    The replacement branch never issues a second disposition.
    """
    path = Path(path)
    root = Path(root)
    if not contained(root, path):
        return Outcome(REFUSED, str(path), expected_identity, note="path is outside the authorized root")
    if expected_kind not in {"file", "directory"}:
        return Outcome(REFUSED, str(path), expected_identity, note="expected kind is not a file or directory")
    if not delays or len(delays) > 8:
        return Outcome(REFUSED, str(path), expected_identity, note="retry schedule is missing or unbounded")

    found = lookup(path)
    if found.state == MISSING:
        return Outcome(MISSING, str(path), expected_identity, note="target is already absent")
    if found.state == UNEXPECTED_OBJECT or found.kind == "reparse":
        return Outcome(UNEXPECTED_OBJECT, str(path), expected_identity, found.identity, found.kind, note=found.note or "refusing reparse point")
    if found.state not in {EXISTS_VERIFIED, DELETE_PENDING}:
        return Outcome(DELETE_FAILED, str(path), expected_identity, found.identity, found.kind, note=found.note or "lookup failed before deletion")
    if not same_identity(found.identity, expected_identity):
        return Outcome(
            IDENTITY_MISMATCH, str(path), expected_identity, found.identity, found.kind,
            note="filesystem identity does not match the frozen record; object not touched",
        )
    if found.kind != expected_kind:
        return Outcome(
            UNEXPECTED_OBJECT, str(path), expected_identity, found.identity, found.kind,
            note=f"expected {expected_kind} and found {found.kind}",
        )
    if found.delete_pending:
        return Outcome(
            DELETE_PENDING, str(path), expected_identity, found.identity, found.kind,
            delete_pending=True, note="target is already delete-pending; no second disposition was set",
            phases=[DELETE_PENDING],
        )

    if expected_kind == "directory":
        try:
            with os.scandir(win_path(path)) as scanned:
                children = list(scanned)
        except OSError as exc:
            return Outcome(DELETE_FAILED, str(path), expected_identity, found.identity, "directory", note=f"directory could not be listed: {exc}")
        if children:
            return Outcome(
                UNEXPECTED_OBJECT, str(path), expected_identity, found.identity, "directory",
                note="directory is not empty; no disposition was set",
            )

    access = (GENERIC_READ | DELETE_ACCESS) if expected_kind == "file" else (FILE_READ_ATTRIBUTES | DELETE_ACCESS)
    handle, error = _open(path, access, directory=expected_kind == "directory")
    if handle is None:
        return Outcome(DELETE_FAILED, str(path), expected_identity, found.identity, expected_kind, winerror=error, note=f"delete handle could not be opened: {error}")
    try:
        opened = _read_handle(handle)
        if opened.state != EXISTS_VERIFIED or not same_identity(opened.identity, expected_identity) or opened.kind != expected_kind:
            return Outcome(
                IDENTITY_MISMATCH, str(path), expected_identity, opened.identity, opened.kind,
                note="handle identity changed before the disposition; no disposition was set",
            )
        if expected_kind == "file":
            if expected_size is not None and opened.size != expected_size:
                return Outcome(DELETE_FAILED, str(path), expected_identity, opened.identity, "file", note="size changed before deletion; no disposition was set")
            digest, read_error = _hash_handle(handle)
            if read_error or digest is None:
                return Outcome(DELETE_FAILED, str(path), expected_identity, opened.identity, "file", winerror=read_error, note="content could not be hashed; no disposition was set")
            if expected_sha256 is not None and digest != expected_sha256:
                return Outcome(DELETE_FAILED, str(path), expected_identity, opened.identity, "file", note="SHA-256 changed before deletion; no disposition was set")
        attributes = found.attributes or 0
        if attributes & FILE_ATTRIBUTE_READONLY:
            if not KERNEL.SetFileAttributesW(win_path(path), attributes & ~FILE_ATTRIBUTE_READONLY):
                return Outcome(DELETE_FAILED, str(path), expected_identity, opened.identity, expected_kind, winerror=ctypes.get_last_error(), note="read-only attribute could not be cleared")
            rechecked = _read_handle(handle)
            if not same_identity(rechecked.identity, expected_identity):
                return Outcome(IDENTITY_MISMATCH, str(path), expected_identity, rechecked.identity, rechecked.kind, note="identity changed while clearing read-only")
        disposition = DispositionInfo(1)
        ok = KERNEL.SetFileInformationByHandle(handle, FILE_DISPOSITION_INFO_CLASS, ctypes.byref(disposition), ctypes.sizeof(disposition))
        if not ok:
            return Outcome(
                DELETE_FAILED, str(path), expected_identity, opened.identity, expected_kind,
                winerror=ctypes.get_last_error(), note="FileDispositionInfo was rejected",
                phases=[DELETE_FAILED],
            )
    finally:
        KERNEL.CloseHandle(handle)

    outcome = _confirm(path, expected_identity, delays, lookup)
    outcome.phases = [EXISTS_VERIFIED, DELETE_REQUESTED, *outcome.phases[1:]]
    return outcome


def confirm_absence(path: Path, expected_identity, *, delays=DEFAULT_DELAYS, lookup=lookup_nofollow) -> Outcome:
    """Classify a path after a disposition. This function does not delete."""
    return _confirm(Path(path), expected_identity, delays, lookup)
