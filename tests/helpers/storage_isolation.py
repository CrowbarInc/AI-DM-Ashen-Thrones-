"""Import-safe test storage setup and a fail-closed production-data write guard."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PROTECTED = (ROOT / "data").resolve()
ARTIFACTS = (ROOT / "artifacts").resolve()


def install(root=None):
    """Configure existing persistence before importing game modules; no new store."""
    target = Path(root or tempfile.mkdtemp(prefix="ashen-tests-")).resolve()
    if target == PROTECTED or PROTECTED in target.parents:
        raise ValueError("Test storage must be outside repository data")
    target.mkdir(parents=True, exist_ok=True)
    # Evidence belongs to an explicitly configured run, never a fixed cycle.
    evidence = os.environ.get("ASHEN_TEST_EVIDENCE_DIR")
    if root is not None and ARTIFACTS in target.parents:
        evidence = str(target.parent)
    if not evidence:
        for i, arg in enumerate(sys.argv):
            if arg.startswith("--junitxml="):
                evidence = str(Path(arg.split("=", 1)[1]).resolve().parent)
            elif arg == "--junitxml" and i + 1 < len(sys.argv):
                evidence = str(Path(sys.argv[i + 1]).resolve().parent)
    evidence_root = Path(evidence).resolve() if evidence else None
    if evidence_root == ARTIFACTS:
        raise ValueError("Evidence requires a specific run directory, not all artifacts")
    if evidence_root:
        os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(evidence_root)
    for name in ("campaign.json", "character.json", "world.json", "conditions.json"):
        if not (target / name).exists():
            shutil.copy2(PROTECTED / name, target / name)
    if not (target / "scenes").exists():
        shutil.copytree(PROTECTED / "scenes", target / "scenes")
    os.environ["ASHEN_DATA_DIR"] = str(target)
    os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(target / "provider_usage.jsonl")

    def protected(path):
        if isinstance(path, (str, bytes, os.PathLike)):
            p = Path(os.fsdecode(path)).resolve()
            gameplay = p == PROTECTED or PROTECTED in p.parents
            historical_evidence = (p == ARTIFACTS or ARTIFACTS in p.parents) and not (
                evidence_root and (p == evidence_root or evidence_root in p.parents)
            )
            return gameplay or historical_evidence
        return False

    def guard(event, args):
        paths = ()
        if event == "open":
            path, mode, flags = args
            if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)
            ):
                paths = (path,)
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.truncate", "os.utime"}:
            paths = args[:1]
        elif event in {"os.rename", "os.link", "os.symlink"}:
            paths = args[:2]
        if any(protected(p) for p in paths):
            raise PermissionError("Test attempted to modify protected repository data: " + str(paths))

    sys.addaudithook(guard)
    return target
