"""Build the PR-PLAY-13 review archive. No network and no commit."""
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "pr_play_13"
REPORTS = ROOT / "development" / "campaigns" / "product_realization" / "pr_play_13"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
SNAP = OUT / "source_snapshots"
SNAP.mkdir(exist_ok=True)

tracked = [
    "game/gm.py",
    "game/api.py",
    "tools/playtest/worker.py",
    "tools/playtest/runner.py",
    "docs/NEXT_SESSION.md",
]
new_files = [
    "game/opening_presentation_renderer.py",
    "tests/test_pr_play_13_opening_renderer.py",
]
diff = subprocess.run(
    ["git", "diff", "--", *tracked],
    cwd=ROOT,
    capture_output=True,
    text=True,
    check=True,
)
(OUT / "source_diff.patch").write_text(diff.stdout, encoding="utf-8")
status = subprocess.run(["git", "status", "--short"], cwd=ROOT, capture_output=True, text=True, check=True)
revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
(OUT / "repository_status.txt").write_text(
    f"revision: {revision.stdout.strip()}\n\n{status.stdout}",
    encoding="utf-8",
)
for relative in tracked + new_files:
    source = ROOT / relative
    dest = SNAP / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)

members = []
for path in sorted(REPORTS.glob("*.md")):
    members.append(path)
for relative in [
    "artifacts/pr_play_13/source_diff.patch",
    "artifacts/pr_play_13/repository_status.txt",
    "artifacts/pr_play_13/catalog_entry.schema.json",
    "artifacts/pr_play_13/presentation_plan.schema.json",
    "artifacts/pr_play_13/regression_summary.json",
    "artifacts/pr_play_13/confirmation_runs.json",
    "artifacts/pr_play_13/five_turn_renderer_run.json",
    "game/opening_presentation_renderer.py",
    "tests/test_pr_play_13_opening_renderer.py",
    "handoff/CURRENT_REVIEW.md",
    "docs/NEXT_SESSION.md",
]:
    members.append(ROOT / relative)
for path in SNAP.rglob("*"):
    if path.is_file():
        members.append(path)

history = ROOT / "handoff" / "history" / "pr_play_13"
history.mkdir(parents=True, exist_ok=True)
shutil.copy2(ROOT / "handoff" / "CURRENT_REVIEW.md", history / "REVIEW.md")

manifest_rows = []
for path in members:
    data = path.read_bytes()
    if re.search(br"sk-[A-Za-z0-9]{20,}", data):
        raise SystemExit(f"secret-like content in {path}")
    manifest_rows.append({
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })

manifest = {
    "campaign": "pr_play_13",
    "generated": datetime.now().astimezone().isoformat(),
    "revision": revision.stdout.strip(),
    "verdict": "B — Conditionally ready for controlled live validation",
    "files": manifest_rows,
}
(ROOT / "handoff" / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
shutil.copy2(ROOT / "handoff" / "REVIEW_MANIFEST.json", history / "REVIEW_MANIFEST.json")

def write_zip(destination: Path) -> None:
    with ZipFile(destination, "w", compression=ZIP_DEFLATED) as archive:
        archive.write(ROOT / "handoff" / "CURRENT_REVIEW.md", "CURRENT_REVIEW.md")
        archive.write(ROOT / "handoff" / "REVIEW_MANIFEST.json", "REVIEW_MANIFEST.json")
        for row in manifest_rows:
            archive.write(ROOT / row["path"], row["path"])

timestamped = ROOT / "handoff" / f"CURRENT_REVIEW({STAMP}).zip"
stable = ROOT / "handoff" / "CURRENT_REVIEW.zip"
write_zip(timestamped)
shutil.copy2(timestamped, stable)
shutil.copy2(timestamped, history / f"CURRENT_REVIEW({STAMP}).zip")
print(timestamped)
print(timestamped.stat().st_size)
