"""Package PR-PLAY-40 evidence. Does not import the application or call a provider."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REVIEW = ROOT / "handoff" / "CURRENT_REVIEW.md"

INCLUDE = [
    REVIEW,
    OUT / "diagnose_travel.py",
    OUT / "travel_diagnosis.json",
    OUT / "travel_regression_baseline.txt",
    OUT / "regression_results.txt",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    from dotenv import dotenv_values
    import os

    env = {**dotenv_values(ROOT / ".env"), **os.environ}
    hidden = [
        value.encode()
        for key, value in env.items()
        if isinstance(value, str)
        and len(value) > 8
        and any(part in key.lower() for part in ("key", "token", "secret", "password", "credential"))
    ]
    missing = [str(path) for path in INCLUDE if not path.is_file()]
    if missing:
        raise SystemExit("missing evidence: " + ", ".join(missing))
    hits = []
    for path in INCLUDE:
        blob = path.read_bytes()
        if any(secret in blob for secret in hidden):
            hits.append(str(path.relative_to(ROOT)))
    scan = {"files_scanned": len(INCLUDE), "credential_hits": hits, "passed": not hits}
    scan_path = OUT / "credential_scan.json"
    scan_path.write_text(json.dumps(scan, indent=2) + "\n", encoding="utf-8")
    if hits:
        raise SystemExit("credential scan failed")
    included = [*INCLUDE, scan_path]

    def arcname(path: Path) -> str:
        if path == REVIEW:
            return "CURRENT_REVIEW.md"
        return path.relative_to(OUT).as_posix()

    manifest = {arcname(path): {"bytes": path.stat().st_size, "sha256": sha(path)} for path in included}
    manifest_path = OUT / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    included.append(manifest_path)
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT / "handoff" / f"CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip"
    with zipfile.ZipFile(archive, "x", zipfile.ZIP_DEFLATED) as bundle:
        for path in included:
            bundle.write(path, arcname(path))
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        stored = json.loads(bundle.read("MANIFEST.json"))
        assert all(hashlib.sha256(bundle.read(name)).hexdigest() == row["sha256"] for name, row in stored.items())
    (OUT / "archive_verification.json").write_text(
        json.dumps(
            {
                "path": str(archive),
                "entries": len(included),
                "bytes": archive.stat().st_size,
                "sha256": sha(archive),
                "testzip": None,
                "manifest_hashes_verified": True,
                "verdict": "A — PASS",
                "provider_requests": 0,
                "provider_tokens": 0,
                "live_gameplay_turns": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "archive_path.txt").write_text(str(archive) + "\n", encoding="utf-8")
    print(archive)


if __name__ == "__main__":
    main()
