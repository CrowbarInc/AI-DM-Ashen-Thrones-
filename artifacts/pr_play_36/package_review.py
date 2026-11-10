"""Package PR-PLAY-36 evidence. Does not call a provider or start a campaign."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
EVIDENCE = (
    ROOT
    / "artifacts"
    / "atgb"
    / "pr_play_35"
    / "live"
    / "20261102T011549Z-bd0c88693cd0"
    / "opening_response_evidence"
    / "e97b9ce72d9b494db77178582be66ceb-1.json"
)
TEST = ROOT / "tests" / "test_pr_play_36_opening_rejection.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    hidden: list[bytes] = []
    try:
        from dotenv import dotenv_values

        env = {**dotenv_values(ROOT / ".env"), **os.environ}
    except Exception:
        env = dict(os.environ)
    for key, value in env.items():
        if isinstance(value, str) and len(value) > 8 and any(
            part in key.lower() for part in ("key", "token", "secret", "password", "credential")
        ):
            hidden.append(value.encode())

    included = [
        path
        for path in OUT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and "_replay_store" not in path.parts
        and path.name not in {"archive_path.txt", "archive_verification.json", "MANIFEST.json", "credential_scan.json"}
    ]
    included.extend([EVIDENCE, TEST])
    hits = []
    for path in included:
        blob = path.read_bytes()
        if any(secret in blob for secret in hidden):
            hits.append(str(path.relative_to(ROOT)))
    (OUT / "credential_scan.json").write_text(
        json.dumps({"files_scanned": len(included), "credential_hits": hits, "passed": not hits}, indent=2) + "\n",
        encoding="utf-8",
    )
    if hits:
        raise SystemExit("credential scan failed")
    included.append(OUT / "credential_scan.json")

    def arcname(path: Path) -> str:
        if path == EVIDENCE:
            return "evidence/opening_response_evidence/" + path.name
        if path == TEST:
            return "tests/" + path.name
        return path.relative_to(OUT).as_posix()

    manifest = {arcname(path): {"bytes": path.stat().st_size, "sha256": sha(path)} for path in included}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    included.append(OUT / "MANIFEST.json")

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
    print(json.dumps({"archive": str(archive), "entries": len(included), "verdict": "A — PASS"}))


if __name__ == "__main__":
    main()
