"""Package the PR-PLAY-56 review. Does not call a provider."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_56"
DOCS = (
    "01_EXECUTIVE_SUMMARY.md",
    "02_BASELINE_AND_SCOPE.md",
    "03_SCENARIO_MANIFEST.md",
    "04_PROVIDER_EXECUTION.md",
    "05_RAW_NARRATION_SAMPLES.md",
    "06_VALIDATOR_DECISIONS.md",
    "07_INDEPENDENT_SEMANTIC_REVIEW.md",
    "08_VALIDATOR_ACCURACY.md",
    "09_NARRATION_QUALITY.md",
    "10_FABRICATION_FREQUENCY.md",
    "11_PERFORMANCE_AND_USAGE.md",
    "12_STATE_INTEGRITY.md",
    "13_VALIDATOR_FREEZE_INTEGRITY.md",
    "14_REGRESSION_RESULTS.md",
    "15_LIMITATIONS_AND_OPEN_RISKS.md",
    "16_NEXT_SESSION.md",
)
EXCLUDED_PARTS = {"tmp_runs", "__pycache__", ".pytest_cache"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def credentials() -> list[bytes]:
    found = []
    env_path = ROOT / ".env"
    if not env_path.exists():
        return found
    for line in env_path.read_text(encoding="utf-8-sig").splitlines():
        if "=" not in line or line.lstrip().startswith("#"):
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip("\"'")
        if len(value) > 8 and any(part in key.lower() for part in ("key", "secret", "token", "password")):
            found.append(value.encode())
    return found


def main() -> int:
    missing = [name for name in DOCS if not (OUT / name).exists()]
    if missing:
        raise SystemExit("missing docs: " + ", ".join(missing))
    secrets = credentials()
    paths = []
    for path in sorted(OUT.rglob("*")):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        if path.suffix == ".pyc":
            continue
        if path.name in {"credential_scan.json", "MANIFEST.json", "archive_verification.json", "archive_path.txt"}:
            continue
        paths.append(path)
    hits = []
    for path in paths:
        blob = path.read_bytes()
        if any(secret in blob for secret in secrets) or re.search(br"sk-[A-Za-z0-9]{12,}", blob):
            hits.append(path.relative_to(OUT).as_posix())
    if hits:
        raise SystemExit("credential scan failed: " + ", ".join(hits))
    scan = {"passed": True, "files_scanned": len(paths), "hits": []}
    (OUT / "credential_scan.json").write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")
    paths.append(OUT / "credential_scan.json")
    manifest = {
        path.relative_to(OUT).as_posix(): {"sha256": sha(path), "bytes": path.stat().st_size}
        for path in paths
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    paths.append(OUT / "MANIFEST.json")
    report = (OUT / "01_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8")
    moment = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT / "handoff" / f"CURRENT_REVIEW({moment:%Y%m%d-%H%M%S}).zip"
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as handle:
        for path in paths:
            handle.write(path, path.relative_to(OUT).as_posix())
    with zipfile.ZipFile(archive) as handle:
        bad = handle.testzip()
        if bad is not None:
            raise SystemExit("crc failed: " + bad)
        stored = json.loads(handle.read("MANIFEST.json"))
        for name, row in stored.items():
            if hashlib.sha256(handle.read(name)).hexdigest() != row["sha256"]:
                raise SystemExit("manifest mismatch: " + name)
    handoff = ROOT / "handoff"
    for name, content in (("CURRENT_REVIEW.zip", archive.read_bytes()), ("CURRENT_REVIEW.md", report.encode("utf-8"))):
        pending = handoff / ("PR_PLAY_56_pending_" + name)
        pending.write_bytes(content)
        pending.replace(handoff / name)
    verification = {
        "archive": str(archive),
        "sha256": sha(archive),
        "stable_archive": str(handoff / "CURRENT_REVIEW.zip"),
        "stable_archive_matches": sha(archive) == sha(handoff / "CURRENT_REVIEW.zip"),
        "crc_valid": True,
        "manifest_hashes_valid": True,
        "entries": len(paths),
        "bytes": archive.stat().st_size,
    }
    (OUT / "archive_verification.json").write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    (OUT / "archive_path.txt").write_text(str(archive) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
