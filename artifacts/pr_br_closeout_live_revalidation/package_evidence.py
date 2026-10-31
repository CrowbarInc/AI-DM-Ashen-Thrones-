"""Package the closeout revalidation. No gameplay imports and no model calls."""
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
HANDOFF = ROOT / "handoff"


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


calls = read("model_calls.json")
http = read("http_attempts.json")
finished = read("run_finished.json")
input_tokens = sum((c.get("usage") or {}).get("input_tokens") or 0 for c in calls)
output_tokens = sum((c.get("usage") or {}).get("output_tokens") or 0 for c in calls)
summary = {
    "validation": "PR-BR closeout live revalidation",
    "decision": "A",
    "decision_text": (
        "PR-BR CLOSEOUT RECOMMENDED; "
        "SYSTEMIC SEMANTIC/AUTHORITY BOUNDARY IS SUFFICIENTLY STABLE. "
        "MOVE REMAINING ISSUES TO LATER AI, GAMEPLAY, OR PRODUCT CAMPAIGNS."
    ),
    "gameplay_turns": finished["turns"],
    "halt": finished["halt"],
    "preflight_calls": sum(1 for c in calls if c.get("kind") == "preflight"),
    "interpretation_calls": sum(1 for c in calls if c.get("kind") == "interpretation"),
    "initial_generation_calls": 4,
    "retry_generation_calls": 4,
    "other_model_calls": 0,
    "total_model_calls": len(calls),
    "http_attempts": len(http),
    "http_statuses": [h.get("status") for h in http],
    "bounded_keep_invocations": finished["bounded_keep"],
    "provider_input_tokens": input_tokens,
    "provider_output_tokens": output_tokens,
    "provider_total_tokens": input_tokens + output_tokens,
    "generated_utc": datetime.now(timezone.utc).isoformat(),
}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

history = HANDOFF / "history" / "pr-br-before-closeout-live-revalidation"
history.mkdir(parents=True, exist_ok=True)
for name in ("CURRENT_REVIEW.zip", "CURRENT_REVIEW.md", "REVIEW_MANIFEST.json"):
    source = HANDOFF / name
    target = history / name
    if source.exists() and not target.exists():
        shutil.copy2(source, target)

shutil.copy2(OUT / "REPORT.md", HANDOFF / "CURRENT_REVIEW.md")

files = {"CURRENT_REVIEW.md": HANDOFF / "CURRENT_REVIEW.md"}
for path in OUT.rglob("*"):
    if not path.is_file() or "__pycache__" in path.parts:
        continue
    files["evidence/" + path.relative_to(OUT).as_posix()] = path

manifest = {
    "validation": summary["validation"],
    "generated_utc": summary["generated_utc"],
    **summary,
    "files": [
        {
            "path": name,
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
        for name, path in sorted(files.items())
    ],
}
(HANDOFF / "REVIEW_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
files["REVIEW_MANIFEST.json"] = HANDOFF / "REVIEW_MANIFEST.json"

zip_path = HANDOFF / "CURRENT_REVIEW.zip"
if zip_path.exists():
    zip_path.unlink()
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
    for name, path in sorted(files.items()):
        archive.write(path, name)
with zipfile.ZipFile(zip_path) as archive:
    bad = archive.testzip()
    if bad:
        raise SystemExit(f"bad zip entry {bad}")
    for row in manifest["files"]:
        digest = hashlib.sha256(archive.read(row["path"])).hexdigest()
        if digest != row["sha256"]:
            raise SystemExit(f"hash mismatch {row['path']}")
print(json.dumps({
    "zip": str(zip_path),
    "bytes": zip_path.stat().st_size,
    "entries": len(files),
    "crc_and_sha256": "PASS",
    "summary": summary,
}, indent=2))
