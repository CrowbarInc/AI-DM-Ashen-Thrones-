"""Package PR-PLAY-35 evidence. Does not launch a worker or call a provider."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RUN = ROOT / "artifacts" / "atgb" / "pr_play_35" / "live" / "20261102T011549Z-bd0c88693cd0"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from dotenv import dotenv_values
    import os
    env = {**dotenv_values(ROOT / ".env"), **os.environ}
    hidden = [value.encode() for key, value in env.items()
              if isinstance(value, str) and len(value) > 8
              and any(part in key.lower() for part in ("key", "token", "secret", "password", "credential"))]
    included = [path for path in OUT.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
                and path.name not in {"archive_path.txt", "archive_verification.json", "MANIFEST.json", "credential_scan.json"}]
    included.extend(path for path in RUN.rglob("*")
                    if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".zip")
    hits = []
    for path in included:
        blob = path.read_bytes()
        if any(secret in blob for secret in hidden):
            hits.append(str(path.relative_to(ROOT)))
    (OUT / "credential_scan.json").write_text(json.dumps({
        "files_scanned": len(included), "credential_hits": hits, "passed": not hits}, indent=2) + "\n", encoding="utf-8")
    if hits:
        raise SystemExit("credential scan failed")
    included.append(OUT / "credential_scan.json")

    def arcname(path):
        if path.is_relative_to(RUN):
            return "evidence/live/" + path.relative_to(RUN).as_posix()
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
    (OUT / "archive_verification.json").write_text(json.dumps({
        "path": str(archive), "entries": len(included), "bytes": archive.stat().st_size,
        "sha256": sha(archive), "testzip": None, "manifest_hashes_verified": True,
        "verdict": "C — FAIL"}, indent=2) + "\n", encoding="utf-8")
    (OUT / "archive_path.txt").write_text(str(archive) + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "entries": len(included), "verdict": "C — FAIL"}))


if __name__ == "__main__":
    main()
