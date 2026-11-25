"""Corrected AT-FG-05 continuation executor.

Historical deletion is refused in this milestone. The only removal path is an
R1 fixture under development/tmp that carries the fixture secret written by
allocate_fixture. The frozen manifest and ledger are read, never rewritten.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "at_fg_05_r1_ntfs", Path(__file__).with_name("ntfs_disposition.py")
)
ntfs = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = ntfs
_SPEC.loader.exec_module(ntfs)

EXECUTOR_VERSION = ntfs.EXECUTOR_VERSION
REPO = Path(__file__).resolve().parents[2]
TMP = REPO / "development" / "tmp"
MARKER = ".ashen-r1-fixture"
MANIFEST = REPO / "development" / "reports" / "AT-FG-05_CLEANUP_MANIFEST.json"
LEDGER = REPO / "development" / "reports" / "AT-FG-05_EXEC_LEDGER.json"
MANIFEST_SHA = "2d01b45dc151266960ae4b4765f19935919b14577f1a72a2bcaef3955e80b638"
INVENTORY_SHA = "058a2067251f49f3d02ad849823cf6ae65aabd194ca4027b562cb85592dc6045"


class ContinuationRefused(RuntimeError):
    pass


def allocate_fixture(parent: Path) -> Path:
    parent = Path(parent)
    if TMP not in parent.parents and parent != TMP:
        raise ContinuationRefused("fixtures must be created under development/tmp")
    root = Path(os.path.join(parent, f"at-fg-05-r1-{os.urandom(4).hex()}"))
    root.mkdir()
    (root / MARKER).write_text(os.urandom(16).hex(), encoding="ascii")
    return root


def _owned(root: Path) -> bool:
    root = Path(root)
    if TMP not in root.parents:
        return False
    if "artifacts" in root.parts or "campaigns" in root.parts:
        return False
    marker = root / MARKER
    try:
        metadata = os.lstat(marker)
    except OSError:
        return False
    if not metadata.st_size or bool(getattr(metadata, "st_file_attributes", 0) & 0x400):
        return False
    return root.name.startswith("at-fg-05-r1-")


def discard_fixture(root: Path) -> None:
    if not _owned(root):
        raise ContinuationRefused("refusing to remove a path this harness does not own")
    import shutil
    shutil.rmtree(root)


def resume_historical(plan: dict) -> dict:
    """Public entry. R1 never deletes historical targets from this function."""
    authorized = bool(plan.get("continuation_authorized") is True)
    return {
        "continuation_authorized": False,
        "deleted": [],
        "executor_version": EXECUTOR_VERSION,
        "historical_deletion_performed": False,
        "status": "REFUSED",
        "reason": "continuation_authorized is false" if not authorized else "R1 does not execute historical deletion",
    }


def delete_in_fixture(root: Path, path: Path, *, expected_identity, expected_kind: str, expected_sha256=None, expected_size=None, delays=None) -> dict:
    root = Path(root)
    path = Path(path)
    if not _owned(root):
        raise ContinuationRefused("deletion root is not an R1 fixture")
    if TMP not in Path(os.path.abspath(path)).parents:
        raise ContinuationRefused("target is not under development/tmp")
    historical = REPO / "artifacts"
    campaigns = REPO / "development" / "campaigns"
    absolute = Path(os.path.abspath(path))
    if historical in absolute.parents or absolute == historical or campaigns in absolute.parents or absolute == campaigns:
        raise ContinuationRefused("historical evidence is outside fixture deletion")
    kwargs = {}
    if delays is not None:
        kwargs["delays"] = delays
    outcome = ntfs.delete_exact(
        path, root=root, expected_identity=expected_identity, expected_kind=expected_kind,
        expected_sha256=expected_sha256, expected_size=expected_size, **kwargs,
    )
    return outcome.as_dict()


def append_recovery(root: Path, record: dict) -> Path:
    if not _owned(root):
        raise ContinuationRefused("recovery log root is not an R1 fixture")
    log = Path(root) / "recovery.jsonl"
    with log.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return log


def frozen_hashes() -> dict:
    import hashlib
    manifest = MANIFEST.read_bytes()
    inventory = (REPO / "artifacts" / "at_fg_05_preflight" / "AT-FG-05_EXACT_TARGETS.jsonl.gz").read_bytes()
    return {
        "inventory_sha256": hashlib.sha256(inventory).hexdigest(),
        "inventory_sha256_matches": hashlib.sha256(inventory).hexdigest() == INVENTORY_SHA,
        "ledger_present": LEDGER.is_file(),
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "manifest_sha256_matches": hashlib.sha256(manifest).hexdigest() == MANIFEST_SHA,
    }


def main() -> int:
    result = resume_historical({"continuation_authorized": False, "manifest_sha256": MANIFEST_SHA})
    print(json.dumps(result))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
