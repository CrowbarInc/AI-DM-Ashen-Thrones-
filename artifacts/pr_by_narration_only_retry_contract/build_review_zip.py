"""Refresh handoff/CURRENT_REVIEW.zip for PR-BY. No model calls."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GATE = ROOT / "artifacts" / "pr_by_narration_only_retry_contract"
ZIP_PATH = ROOT / "handoff" / "CURRENT_REVIEW.zip"

FILES = [
    ROOT / "handoff" / "CURRENT_REVIEW.md",
    ROOT / "handoff" / "REVIEW_MANIFEST.json",
    GATE / "PR-BY_narration_only_retry_contract_report.md",
    GATE / "PR-BY_retry_path_audit.md",
    GATE / "PR-BY_retry_contract_matrix.json",
    GATE / "pr_bx_retry_feedback_snapshot.json",
    GATE / "focused_tests.txt",
    GATE / "broad_tests.txt",
    GATE / "changed_files.txt",
    GATE / "capture_evidence.py",
    ROOT / "tests" / "test_pr_by_narration_only_retry_contract.py",
]


def main() -> None:
    missing = [str(path) for path in FILES if not path.is_file()]
    if missing:
        raise SystemExit("missing:\n" + "\n".join(missing))
    blob = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in FILES)
    if "sk-" in blob:
        raise SystemExit("refusing to zip evidence that contains an API key prefix")
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    manifest = []
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in FILES:
            data = path.read_bytes()
            if path.name == "CURRENT_REVIEW.md":
                arc = "CURRENT_REVIEW.md"
            else:
                arc = path.relative_to(ROOT).as_posix()
            archive.writestr(arc, data)
            manifest.append({"path": arc, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
        body = {
            "review": "PR-BY narration-only retry contract preservation",
            "mode": "NARRATION-ONLY RETRY CONTRACT PRESERVATION",
            "model_api_calls": 0,
            "decision": "A",
            "decision_label": "RETRY CONTRACT PRESERVATION READY FOR MICRO LIVE",
            "narration_only_retry_expected_keys": ["narration"],
            "narration_only_retry_declared_claims_exposed": False,
            "narration_only_retry_structured_envelope_schema_exposed": False,
            "files": manifest,
        }
        archive.writestr("ZIP_MANIFEST.json", json.dumps(body, indent=2).encode("utf-8"))
    print(f"wrote {ZIP_PATH} files={len(FILES) + 1} bytes={ZIP_PATH.stat().st_size}")


if __name__ == "__main__":
    main()
