"""Refresh handoff/CURRENT_REVIEW.zip for the final micro-live gate. No model calls."""
import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "artifacts" / "pr_bt_selective_epistemic_restoration_final_micro_live" / "evidence"
ZIP_PATH = ROOT / "handoff" / "CURRENT_REVIEW.zip"
MANIFEST_PATH = ROOT / "handoff" / "REVIEW_MANIFEST.json"

ROOT_FILES = [
    "handoff/CURRENT_REVIEW.md",
    "PR-BT_selective_epistemic_restoration_final_micro_live.md",
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
    files = [ROOT / item for item in ROOT_FILES] + evidence_files()
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise SystemExit("missing:\n" + "\n".join(missing))
    manifest = []
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
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
            "review": "PR-BT selective epistemic restoration final micro-live",
            "mode": "FINAL MICRO LIVE",
            "model_api_calls": 5,
            "gameplay_generations": 4,
            "retry_count": 1,
            "decision": "C - SELECTIVE RESTORATION INSUFFICIENT",
            "architecture": "A - PR-BR REMAINS CLOSED",
            "initial_input_tokens": {"P1": 21952, "P2": 24534, "P3": 21977},
            "complete_turn_input_tokens": 91704,
            "vs_pr_bs_complete_turn_input": 13468,
            "vs_failed_pr_bt_complete_turn_input": -22785,
            "first_pass_acceptance": "2/3",
            "useful_first_pass": "1/3",
            "c18": "PASS",
            "authority_integrity": "HELD",
            "validators_changed": False,
            "retry_changed": False,
            "files": manifest,
        }
        encoded = json.dumps(body, indent=2).encode("utf-8")
        archive.writestr("REVIEW_MANIFEST.json", encoded)
    MANIFEST_PATH.write_bytes(encoded)
    print(f"wrote {ZIP_PATH} files={len(manifest)+1} bytes={ZIP_PATH.stat().st_size}")


if __name__ == "__main__":
    main()
