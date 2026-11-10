"""Read-only PR-PLAY-79D-F baseline. Does not import the game or write protected data."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PRIOR = ROOT / "artifacts" / "pr_play_79d" / "review" / "machine" / "protected_after.json"
SOURCE = [
    "game/api.py",
    "game/api_turn_support.py",
    "game/bounded_improvisation.py",
    "game/controlled_investigation_renderer.py",
    "game/exploration.py",
    "game/expressive_dialogue.py",
    "game/integrated_play.py",
    "game/physical_adjudication.py",
    "game/player_http_boundary.py",
    "game/publication_contract.py",
    "game/quarantined_investigation_narration.py",
    "static/app.js",
    "static/index.html",
    "tests/conftest.py",
    "tests/helpers/storage_isolation.py",
    "tests/test_pr_play_79d_closeout.py",
    "tests/test_pr_play_79d_holdout.py",
]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True, encoding="utf-8", errors="replace")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    files = []
    changed = []
    for row in prior["files"]:
        path = ROOT / row["path"]
        current = sha(path) if path.is_file() else None
        item = {
            "path": row["path"],
            "entry_sha256": current,
            "bytes": path.stat().st_size if path.is_file() else None,
            "prior_sha256": row.get("current_sha256") or row.get("sha256"),
            "unchanged_vs_79d_close": current == (row.get("current_sha256") or row.get("sha256")),
        }
        files.append(item)
        if not item["unchanged_vs_79d_close"]:
            changed.append(row["path"])
    protected = {"count": len(files), "preserved_vs_79d_close": len(files) - len(changed), "changed": changed, "files": files}
    (OUT / "protected_entry.json").write_text(json.dumps(protected, indent=2), encoding="utf-8")

    sources = []
    for rel in SOURCE:
        path = ROOT / rel
        sources.append({"path": rel, "sha256": sha(path), "bytes": path.stat().st_size})
    diff = git("diff")
    diff_hash = hashlib.sha256(diff.encode("utf-8")).hexdigest()
    (OUT / "working_tree.diff").write_text(diff, encoding="utf-8")
    status = git("status", "--short")
    (OUT / "git_status.txt").write_text(status, encoding="utf-8")
    fingerprint = {
        "cycle": "PR-PLAY-79D-F",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD").strip(),
        "head": git("rev-parse", "HEAD").strip(),
        "working_tree_diff_sha256": diff_hash,
        "working_tree_diff_bytes": len(diff.encode("utf-8")),
        "status_entries": len([line for line in status.splitlines() if line.strip()]),
        "protected_count": protected["count"],
        "protected_preserved_vs_79d_close": protected["preserved_vs_79d_close"],
        "protected_changed": changed,
        "sources": sources,
        "application_source_frozen": True,
        "note": "Fingerprint taken before PR-PLAY-79D-F test or evidence edits.",
    }
    (OUT / "source_fingerprint.json").write_text(json.dumps(fingerprint, indent=2), encoding="utf-8")

    session_path = ROOT / "artifacts" / "pr_play_79d" / "browser_data" / "session.json"
    summary = {"session_present": session_path.is_file()}
    if session_path.is_file():
        session = json.loads(session_path.read_text(encoding="utf-8"))
        ledger = session.get("bounded_improvisation") or session.get("bounded_improvisation_ledger") or {}
        if not isinstance(ledger, dict):
            ledger = {}
        summary.update({
            "active_scene_id": session.get("active_scene_id"),
            "turn_counter": session.get("turn_counter"),
            "campaign_run_id": session.get("campaign_run_id"),
            "active_interlocutor": session.get("active_interlocutor"),
            "clue_ids": sorted((session.get("clue_knowledge") or {}).keys()) if isinstance(session.get("clue_knowledge"), dict) else [],
            "position": ledger.get("position"),
            "posture": ledger.get("posture"),
            "session_sha256": sha(session_path),
        })
    (OUT / "campaign_state_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({
        "head": fingerprint["head"],
        "protected": f"{protected['preserved_vs_79d_close']}/{protected['count']}",
        "changed": changed,
        "diff_sha256": diff_hash,
        "scene": summary.get("active_scene_id"),
        "position": summary.get("position"),
        "clues": summary.get("clue_ids"),
    }, indent=2))


if __name__ == "__main__":
    main()
