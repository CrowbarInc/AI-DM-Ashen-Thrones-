"""Package the PR-PLAY-50 review. No provider calls and no campaign writes."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_50"
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    report_path = OUT / "PR_PLAY_50_REPORT.md"
    report = report_path.read_bytes()
    predecessor = OUT / "predecessor"
    predecessor.mkdir(exist_ok=True)
    for name in ("CURRENT_REVIEW.md", "CURRENT_REVIEW.zip"):
        source = ROOT / "handoff" / name
        if source.exists() and not (predecessor / name).exists():
            shutil.copy2(source, predecessor / name)
    credentials = []
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            if len(value) > 8 and any(part in key.lower() for part in ("key", "secret", "token", "password")):
                credentials.append(value.encode())
    excluded_names = {"MANIFEST.json", "archive_verification.json", "credential_scan.json"}
    paths = [
        path for path in OUT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and not (path.parent == OUT and path.name in excluded_names)
    ]
    hits = [path.relative_to(OUT).as_posix() for path in paths if any(secret in path.read_bytes() for secret in credentials)]
    if hits:
        raise SystemExit("credential scan failed")
    scan = {"passed": True, "files_scanned": len(paths), "hits": []}
    (OUT / "credential_scan.json").write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")
    paths.append(OUT / "credential_scan.json")
    manifest = {path.relative_to(OUT).as_posix(): {"sha256": sha(path), "bytes": path.stat().st_size} for path in paths}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    paths.append(OUT / "MANIFEST.json")
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT / "handoff" / f"CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip"
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as handle:
        for path in paths:
            handle.write(path, path.relative_to(OUT).as_posix())
        handle.writestr("CURRENT_REVIEW.md", report)
    with zipfile.ZipFile(archive) as handle:
        bad = handle.testzip()
        if bad is not None:
            raise SystemExit("crc failed: " + bad)
        stored = json.loads(handle.read("MANIFEST.json"))
        for name, row in stored.items():
            if hashlib.sha256(handle.read(name)).hexdigest() != row["sha256"]:
                raise SystemExit("manifest mismatch: " + name)
    for name, content in (("CURRENT_REVIEW.zip", archive.read_bytes()), ("CURRENT_REVIEW.md", report)):
        pending = ROOT / "handoff" / ("PR_PLAY_50_pending_" + name)
        pending.write_bytes(content)
        pending.replace(ROOT / "handoff" / name)
    verification = {
        "archive": str(archive),
        "sha256": sha(archive),
        "stable_archive": str(ROOT / "handoff" / "CURRENT_REVIEW.zip"),
        "stable_archive_matches": sha(archive) == sha(ROOT / "handoff" / "CURRENT_REVIEW.zip"),
        "crc_valid": True,
        "manifest_hashes_valid": True,
        "entries": len(paths) + 1,
        "bytes": archive.stat().st_size,
    }
    (OUT / "archive_verification.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    (OUT / "archive_path.txt").write_text(str(archive) + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size, "entries": verification["entries"]}, indent=2))


if __name__ == "__main__":
    main()
