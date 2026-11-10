"""Package the PR-PLAY-42 review. Does not call a provider."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REVIEW = ROOT / "handoff" / "CURRENT_REVIEW.md"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    included = [
        REVIEW,
        OUT / "baseline_reproduction.txt",
        OUT / "results.json",
        ROOT / "tests" / "test_pr_play_42_evidence_boundaries.py",
    ]
    missing = [path for path in included if not path.is_file()]
    if missing:
        raise SystemExit("missing " + ", ".join(str(path) for path in missing))
    now = datetime.now(timezone(timedelta(hours=-5)))
    archive = ROOT / "handoff" / f"CURRENT_REVIEW({now:%Y%m%d-%H%M%S}).zip"

    def arcname(path: Path) -> str:
        if path == REVIEW:
            return "CURRENT_REVIEW.md"
        if path.parent == OUT:
            return "pr_play_42/" + path.name
        return "tests/" + path.name

    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in included:
            bundle.write(path, arcname(path))
    with zipfile.ZipFile(archive) as bundle:
        bad = bundle.testzip()
        if bad:
            raise SystemExit("corrupt zip entry " + bad)
    (OUT / "archive_path.txt").write_text(str(archive) + "\n", encoding="utf-8")
    print(archive)


if __name__ == "__main__":
    main()
