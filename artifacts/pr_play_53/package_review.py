"""Package the PR-PLAY-53 review. Does not call a provider."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_53"
SOURCE = (
    ROOT / "game" / "quarantined_investigation_narration.py",
    ROOT / "tests" / "test_pr_play_53_quarantined_live.py",
)


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


def review_text() -> str:
    summary = (OUT / "01_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8").strip()
    index = "\n".join(
        f"- `{name}`"
        for name in (
            "01_EXECUTIVE_SUMMARY.md",
            "02_BASELINE_AND_SCOPE.md",
            "03_PROVIDER_CONFIGURATION.md",
            "04_SCENARIO_RESULTS.md",
            "05_NARRATION_EVALUATION.md",
            "06_FABRICATION_VALIDATION.md",
            "07_STATE_INTEGRITY.md",
            "08_PERFORMANCE_AND_USAGE.md",
            "09_TEST_RESULTS.md",
            "10_FINDINGS_AND_RECOMMENDATIONS.md",
            "11_NEXT_SESSION.md",
        )
    )
    return summary + "\n\n## Package files\n\n" + index + "\n"


def main() -> int:
    source_dir = OUT / "source"
    source_dir.mkdir(exist_ok=True)
    for path in SOURCE:
        shutil.copy2(path, source_dir / path.name)
    predecessor = OUT / "predecessor"
    predecessor.mkdir(exist_ok=True)
    for name in ("CURRENT_REVIEW.md", "CURRENT_REVIEW.zip"):
        source = ROOT / "handoff" / name
        if source.exists() and not (predecessor / name).exists():
            shutil.copy2(source, predecessor / name)
    report = review_text()
    (OUT / "CURRENT_REVIEW.md").write_text(report, encoding="utf-8")
    secrets = credentials()
    excluded = {"MANIFEST.json", "archive_verification.json", "credential_scan.json"}
    paths = []
    for path in OUT.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or "tmp_runs" in path.parts:
            continue
        if path.parent == OUT and path.name in excluded:
            continue
        paths.append(path)
    hits = []
    for path in paths:
        blob = path.read_bytes()
        if any(secret in blob for secret in secrets):
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
        pending = handoff / ("PR_PLAY_53_pending_" + name)
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
