"""Refresh handoff/CURRENT_REVIEW.zip for the PR-BX micro-live gate."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "artifacts" / "pr_bx_narration_only_micro_live"
EVIDENCE = GATE / "evidence"
ZIP_PATH = ROOT / "handoff" / "CURRENT_REVIEW.zip"

ROOT_FILES = [
    ROOT / "handoff" / "CURRENT_REVIEW.md",
    ROOT / "handoff" / "REVIEW_MANIFEST.json",
    GATE / "PR-BX_narration_only_micro_live_report.md",
    GATE / "PR-BX_live_probe_matrix.json",
    GATE / "PR-BX_token_retry_comparison.json",
    GATE / "PR-BX_P1_live_evidence.json",
    GATE / "PR-BX_P2_live_evidence.json",
    GATE / "PR-BX_P3_live_evidence.json",
    GATE / "focused_tests.txt",
    GATE / "run_probes.py",
]


def evidence_files() -> list[Path]:
    found = []
    for path in EVIDENCE.rglob("*"):
        if not path.is_file():
            continue
        if "isolated" in path.parts:
            continue
        found.append(path)
    return sorted(found)


def main() -> None:
    files = ROOT_FILES + evidence_files()
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise SystemExit("missing:\n" + "\n".join(missing))
    scanned = [path for path in files if path.suffix.lower() != ".py"]
    blob = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in scanned)
    if "sk-" in blob:
        raise SystemExit("refusing to zip evidence that contains an API key prefix")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    manifest = []
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            data = path.read_bytes()
            if path.name == "CURRENT_REVIEW.md":
                arc = "CURRENT_REVIEW.md"
            else:
                arc = path.relative_to(ROOT).as_posix()
            archive.writestr(arc, data)
            manifest.append({"path": arc, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        body = {
            "review": "PR-BX narration-only envelope micro-live",
            "mode": "NARRATION-ONLY ENVELOPE MICRO-LIVE GATE",
            "model": "gpt-4.1-mini-2025-04-14",
            "model_api_calls": 7,
            "gameplay_generations": 6,
            "preflight_calls": 1,
            "decision": "C",
            "decision_label": "P2 NARRATION-ONLY CONTRACT NEEDS BOUNDED REPAIR",
            "p2_selected_envelope": "narration_only",
            "p2_retry": True,
            "files": manifest,
        }
        encoded = json.dumps(body, indent=2).encode("utf-8")
        archive.writestr("ZIP_MANIFEST.json", encoded)
    print(f"wrote {ZIP_PATH} files={len(files) + 1} bytes={ZIP_PATH.stat().st_size}")


if __name__ == "__main__":
    main()
