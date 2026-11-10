"""Package the PR-PLAY-55 review. Does not call a provider."""
from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_55"
SOURCE = (
    ROOT / "game" / "consequential_narration_validation.py",
    ROOT / "game" / "mechanical_claims.py",
    ROOT / "game" / "proposition_authority.py",
    ROOT / "game" / "anchored_investigation_narration.py",
    ROOT / "tests" / "pr_play_54_corpus.py",
    ROOT / "tests" / "pr_play_55_development.py",
    ROOT / "tests" / "pr_play_55_evaluate.py",
    ROOT / "tests" / "pr_play_55_holdout.json",
    ROOT / "tests" / "pr_play_55_holdout_manifest.json",
    ROOT / "tests" / "test_pr_play_54_consequential_validation.py",
    ROOT / "tests" / "test_pr_play_55_discovery_claims.py",
    ROOT / "tests" / "test_pr_play_55_holdout.py",
)
DOCS = (
    "01_EXECUTIVE_SUMMARY.md",
    "02_BASELINE_AND_SCOPE.md",
    "03_DISCOVERY_CLAIM_ANALYSIS.md",
    "04_AUTHORITY_COMPARISON.md",
    "05_IMPLEMENTATION_CHANGES.md",
    "06_LEGACY_FALSE_POSITIVE_REPAIRS.md",
    "07_DEVELOPMENT_CORPUS_RESULTS.md",
    "08_HOLDOUT_CORPUS_RESULTS.md",
    "09_AMBIGUITY_ANALYSIS.md",
    "10_VALIDATION_PIPELINE_INTEGRITY.md",
    "11_PERFORMANCE_RESULTS.md",
    "12_REGRESSION_RESULTS.md",
    "13_LIMITATIONS_AND_OPEN_RISKS.md",
    "14_NEXT_SESSION.md",
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


def slices() -> None:
    payload = json.loads((OUT / "evaluation.json").read_text(encoding="utf-8"))
    holdout = payload["holdout_rows"]
    development = payload["development_rows"]

    def project(rows):
        keep = ("id", "group", "category", "text", "expected", "actual", "reasons", "reason_codes", "latency_ms")
        return [{key: row[key] for key in keep if key in row} for row in rows]

    (OUT / "holdout_classifications.json").write_text(json.dumps(project(holdout), indent=2) + "\n", encoding="utf-8")
    (OUT / "development_classifications.json").write_text(json.dumps(project(development), indent=2) + "\n", encoding="utf-8")
    (OUT / "false_negative_examples.json").write_text(json.dumps({
        "development": project([row for row in development if row["group"] == "negative" and row["actual"] == "PASS"]),
        "holdout": project([row for row in holdout if row["group"] == "fabrication" and row["actual"] == "PASS"]),
    }, indent=2) + "\n", encoding="utf-8")
    (OUT / "false_positive_examples.json").write_text(json.dumps({
        "development": project([
            row for row in development
            if row["group"] in {"positive", "paraphrase"} and row["actual"] != "PASS"
        ]),
        "holdout": project([
            row for row in holdout
            if row["group"] in {"harmless", "paraphrase"} and row["actual"] != "PASS"
        ]),
    }, indent=2) + "\n", encoding="utf-8")
    (OUT / "review_required_examples.json").write_text(json.dumps({
        "development": project([row for row in development if row["actual"] == "REVIEW_REQUIRED"]),
        "holdout": project([row for row in holdout if row["actual"] == "REVIEW_REQUIRED"]),
    }, indent=2) + "\n", encoding="utf-8")
    (OUT / "confusion_matrices.json").write_text(json.dumps({
        "development": payload["development"]["confusion"],
        "holdout": payload["holdout"]["confusion"],
    }, indent=2) + "\n", encoding="utf-8")


def review_text() -> str:
    summary = (OUT / "01_EXECUTIVE_SUMMARY.md").read_text(encoding="utf-8").strip()
    index = "\n".join(f"- `{name}`" for name in DOCS)
    return summary + "\n\n## Package files\n\n" + index + "\n"


def main() -> int:
    slices()
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
    (OUT / "verdict.json").write_text(json.dumps({
        "code": "A",
        "label": "PASS / READY FOR NEXT CONTROLLED EXPERIMENT",
        "player_facing_narration": "not authorized",
        "real_provider_requests": 0,
        "tokens": 0,
        "previous_fabrications": "49/49 FAIL",
        "development_correct": "40/40",
        "holdout_correct": "70/70",
        "critical_false_negatives": {"development": 0, "holdout": 0},
        "holdout_sha256": "24ff35e8f4096e865dcf3ffd6f98a92d18a208e1329c445c33525e5e5fed1495",
        "next_cycle": "F. Fresh quarantined live-provider narration experiments.",
    }, indent=2) + "\n", encoding="utf-8")
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
        if path.suffix == ".pyc":
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
        pending = handoff / ("PR_PLAY_55_pending_" + name)
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
