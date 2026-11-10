"""Record the PR-PLAY-71V source snapshot. Does not modify product code."""
import hashlib, json, platform, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

SOURCES = [
    "game/api.py",
    "game/authored_consequences.py",
    "game/campaign_reset.py",
    "game/storage.py",
    "game/quarantined_investigation_narration.py",
    "game/player_http_projection.py",
    "static/app.js",
    "tests/test_pr_play_71_lifecycle.py",
    "tests/test_pr_play_71_persistence_recovery.py",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(paths):
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in paths if p.is_file()}


def main():
    prior = json.loads((ROOT / "artifacts/pr_play_71/baseline.json").read_text(encoding="utf-8"))
    protected_now = hashes((ROOT / "data").rglob("*"))
    changed = sorted(p for p, digest in prior.get("protected", {}).items() if protected_now.get(p) != digest)
    missing = sorted(p for p in prior.get("protected", {}) if p not in protected_now)
    freeze = json.loads((ROOT / "artifacts/pr_play_71/final_implementation_freeze.json").read_text(encoding="utf-8"))
    current = {rel: sha(ROOT / rel) for rel in SOURCES}
    data = {
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "system": platform.system(),
        "sources": current,
        "sources_match_pr71_freeze": {rel: current.get(rel) == digest for rel, digest in freeze.items() if rel in current},
        "protected_entries": len(protected_now),
        "protected_changed_since_pr71_baseline": changed,
        "protected_missing_since_pr71_baseline": missing,
        "status_line_count": len(subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True).splitlines()),
    }
    (OUT / "baseline.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps({k: data[k] for k in data if k != "sources"}, indent=2))
    print("sources", json.dumps(data["sources"], indent=2))


if __name__ == "__main__":
    main()
